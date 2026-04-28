from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from chat.models import Message, Survey
from tests.factories import (
    DEFAULT_PASSWORD,
    create_application,
    create_chat_room,
    create_interview,
    create_notification,
    create_stage,
    create_survey_template,
    create_user,
    create_vacancy,
)
from vacancies.models import Application, Interview, Notification, Vacancy


class VacancyModelTests(TestCase):
    def test_models_string_representation(self):
        hr = create_user("vac_hr_model", role=User.Role.HR)
        candidate = create_user("vac_cand_model", role=User.Role.CANDIDATE)
        vacancy = create_vacancy(hr, title="Backend Developer")
        stage = create_stage(vacancy, order=1, title="Скрининг")
        application = create_application(vacancy, candidate)
        interview = create_interview(application, stage)
        notification = create_notification(candidate, title="Тест")

        self.assertEqual(str(vacancy), "Backend Developer")
        self.assertIn("Backend Developer", str(application))
        self.assertIn("Скрининг", str(interview))
        self.assertEqual(str(notification), "Тест")


class VacancyViewTests(TestCase):
    def setUp(self):
        self.hr = create_user("vac_hr_view", role=User.Role.HR)
        self.director = create_user("vac_director_view", role=User.Role.DIRECTOR)
        self.admin = create_user("vac_admin_view", role=User.Role.ADMIN)
        self.candidate = create_user("vac_candidate_view", role=User.Role.CANDIDATE)
        self.other_candidate = create_user("vac_other_candidate", role=User.Role.CANDIDATE)
        self.open_vacancy = create_vacancy(self.hr, title="Open vacancy", status=Vacancy.Status.OPEN)
        self.closed_vacancy = create_vacancy(self.hr, title="Closed vacancy", status=Vacancy.Status.CLOSED)
        self.survey_template = create_survey_template(self.hr, title="Tech Survey")
        self.stage = create_stage(
            self.open_vacancy,
            order=1,
            title="Технический этап",
            survey_template=self.survey_template,
        )
        self.application = create_application(self.open_vacancy, self.candidate)
        self.room = create_chat_room(self.candidate, self.hr)

    def test_candidate_sees_only_open_vacancies(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("vacancies:vacancy_list"))

        self.assertContains(response, "Open vacancy")
        self.assertNotContains(response, "Closed vacancy")

    def test_manager_can_filter_vacancies(self):
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("vacancies:vacancy_list"), {"status": Vacancy.Status.CLOSED})

        self.assertContains(response, "Closed vacancy")
        self.assertNotContains(response, "Open vacancy")

    def test_candidate_can_apply_to_open_vacancy(self):
        self.client.login(username=self.other_candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.post(reverse("vacancies:vacancy_apply", kwargs={"pk": self.open_vacancy.pk}))

        self.assertRedirects(response, reverse("vacancies:vacancy_detail", kwargs={"pk": self.open_vacancy.pk}))
        self.assertTrue(
            Application.objects.filter(vacancy=self.open_vacancy, candidate=self.other_candidate).exists()
        )
        self.assertEqual(Notification.objects.filter(title="Новый отклик").count(), 3)

    def test_duplicate_apply_does_not_create_second_application(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.post(reverse("vacancies:vacancy_apply", kwargs={"pk": self.open_vacancy.pk}))

        self.assertRedirects(response, reverse("vacancies:vacancy_detail", kwargs={"pk": self.open_vacancy.pk}))
        self.assertEqual(
            Application.objects.filter(vacancy=self.open_vacancy, candidate=self.candidate).count(),
            1,
        )

    def test_non_candidate_cannot_apply(self):
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.post(reverse("vacancies:vacancy_apply", kwargs={"pk": self.open_vacancy.pk}))
        self.assertEqual(response.status_code, 403)

    def test_application_status_update_creates_candidate_notification(self):
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("vacancies:application_detail", kwargs={"pk": self.application.pk}),
            {"update_status": "1", "status": Application.Status.OFFER},
        )
        self.application.refresh_from_db()

        self.assertRedirects(
            response,
            reverse("vacancies:application_detail", kwargs={"pk": self.application.pk}),
        )
        self.assertEqual(self.application.status, Application.Status.OFFER)
        self.assertTrue(
            Notification.objects.filter(
                user=self.candidate,
                title="Статус отклика обновлён",
            ).exists()
        )

    def test_schedule_interview_creates_related_entities(self):
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("vacancies:application_detail", kwargs={"pk": self.application.pk}),
            {
                "schedule_interview": "1",
                "stage_id": self.stage.pk,
                "scheduled_at": "2030-01-10T12:30",
            },
        )
        self.application.refresh_from_db()
        interview = Interview.objects.get(application=self.application, stage=self.stage)

        self.assertRedirects(
            response,
            reverse("vacancies:application_detail", kwargs={"pk": self.application.pk}),
        )
        self.assertEqual(self.application.current_stage, self.stage)
        self.assertEqual(self.application.status, Application.Status.INTERVIEW)
        self.assertIsNotNone(interview.survey)
        self.assertEqual(interview.survey.status, Survey.Status.PENDING)
        self.assertTrue(
            Message.objects.filter(
                room=self.room,
                is_system=True,
                text=f"Вам назначен опрос «{self.survey_template.title}» к этапу «{self.stage.title}».",
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(user=self.candidate, title="Собеседование назначено").exists()
        )

    def test_notification_list_marks_unread_as_read(self):
        first = create_notification(self.candidate, title="Unread 1", is_read=False)
        second = create_notification(self.candidate, title="Unread 2", is_read=False)
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("vacancies:notification_list"))

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(first.is_read)
        self.assertTrue(second.is_read)

    def test_unread_notification_count_returns_json(self):
        create_notification(self.candidate, title="Unread", is_read=False)
        create_notification(self.candidate, title="Read", is_read=True)
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("vacancies:unread_notification_count"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
