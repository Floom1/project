from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.decorators import analytics_required, manager_required, role_required
from accounts.forms import ProfileForm
from accounts.models import User
from tests.factories import DEFAULT_PASSWORD, create_user


class UserModelTests(TestCase):
    def test_role_flags_and_permissions(self):
        candidate = create_user("candidate", role=User.Role.CANDIDATE)
        hr = create_user("hr", role=User.Role.HR)
        director = create_user("director", role=User.Role.DIRECTOR)
        admin = create_user("admin_role", role=User.Role.ADMIN)

        self.assertTrue(candidate.is_candidate)
        self.assertFalse(candidate.can_manage)
        self.assertFalse(candidate.can_view_analytics)

        self.assertTrue(hr.is_hr)
        self.assertTrue(hr.can_manage)
        self.assertFalse(hr.can_view_analytics)

        self.assertTrue(director.is_director)
        self.assertTrue(director.can_manage)
        self.assertTrue(director.can_view_analytics)

        self.assertTrue(admin.is_admin_role)
        self.assertTrue(admin.can_manage)
        self.assertTrue(admin.can_view_analytics)

    def test_string_representation_prefers_full_name(self):
        user = create_user("named", first_name="Иван", last_name="Петров")
        self.assertEqual(str(user), "Иван Петров")

    def test_string_representation_falls_back_to_username(self):
        user = create_user("plain", first_name="", last_name="")
        self.assertEqual(str(user), "plain")


class ProfileFormTests(TestCase):
    def test_profile_form_updates_allowed_fields(self):
        user = create_user("profile_user")
        form = ProfileForm(
            data={
                "first_name": "Анна",
                "last_name": "Смирнова",
                "patronymic": "Игоревна",
                "email": "anna@example.com",
                "phone": "+79990001122",
            },
            instance=user,
        )

        self.assertTrue(form.is_valid())
        saved = form.save()
        self.assertEqual(saved.first_name, "Анна")
        self.assertEqual(saved.phone, "+79990001122")

    def test_profile_form_does_not_expose_role_field(self):
        form = ProfileForm()
        self.assertNotIn("role", form.fields)


class DecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.candidate = create_user("candidate_user", role=User.Role.CANDIDATE)
        self.hr = create_user("hr_user", role=User.Role.HR)
        self.director = create_user("director_user", role=User.Role.DIRECTOR)

    def _request(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_role_required_allows_matching_role(self):
        @role_required(User.Role.CANDIDATE)
        def dummy_view(request):
            return HttpResponse("ok")

        response = dummy_view(self._request(self.candidate))
        self.assertEqual(response.status_code, 200)

    def test_role_required_blocks_wrong_role(self):
        @role_required(User.Role.CANDIDATE)
        def dummy_view(request):
            return HttpResponse("ok")

        with self.assertRaises(PermissionDenied):
            dummy_view(self._request(self.hr))

    def test_manager_required_blocks_candidate(self):
        @manager_required
        def dummy_view(request):
            return HttpResponse("ok")

        with self.assertRaises(PermissionDenied):
            dummy_view(self._request(self.candidate))

    def test_analytics_required_allows_director(self):
        @analytics_required
        def dummy_view(request):
            return HttpResponse("ok")

        response = dummy_view(self._request(self.director))
        self.assertEqual(response.status_code, 200)


class AccountViewsTests(TestCase):
    def setUp(self):
        self.candidate = create_user("candidate_view", role=User.Role.CANDIDATE)
        self.hr = create_user("hr_view", role=User.Role.HR)
        self.director = create_user("director_view", role=User.Role.DIRECTOR)
        self.admin = create_user("admin_view", role=User.Role.ADMIN)

    def test_home_redirects_candidate_to_vacancies(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("vacancies:vacancy_list"))

    def test_home_redirects_hr_to_vacancies(self):
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("vacancies:vacancy_list"))

    def test_home_redirects_director_to_analytics(self):
        self.client.login(username=self.director.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("analytics:dashboard"))

    def test_home_redirects_admin_to_analytics(self):
        self.client.login(username=self.admin.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("analytics:dashboard"))

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_profile_get_returns_form(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Профиль")

    def test_profile_post_updates_current_user(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Обновленный",
                "last_name": "Пользователь",
                "patronymic": "Тестович",
                "email": "updated@example.com",
                "phone": "+70000000000",
            },
            follow=True,
        )
        self.candidate.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.candidate.first_name, "Обновленный")
        self.assertContains(response, "Профиль обновлён.")
