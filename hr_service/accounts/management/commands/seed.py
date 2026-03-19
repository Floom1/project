"""
Заполнение БД тестовыми данными для всех модулей.
Запуск: python manage.py seed
"""
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from chat.models import (
    ChatRoom, Message, Survey, SurveyAnswer,
    SurveyQuestion, SurveyTemplate,
)
from documents.models import Document, DocumentApproval, DocumentVersion
from vacancies.models import (
    Application, Interview, InterviewStage,
    Notification, Vacancy,
)


class Command(BaseCommand):
    help = "Заполняет БД тестовыми данными"

    def handle(self, *args, **options):
        self.stdout.write("Создаю пользователей...")
        users = self._create_users()

        self.stdout.write("Создаю шаблоны опросов...")
        templates = self._create_survey_templates(users["hr1"])

        self.stdout.write("Создаю вакансии и этапы...")
        vacancies = self._create_vacancies(users, templates)

        self.stdout.write("Создаю отклики и собеседования...")
        self._create_applications(users, vacancies, templates)

        self.stdout.write("Создаю документы...")
        self._create_documents(users)

        self.stdout.write("Создаю чаты и сообщения...")
        self._create_chats(users, templates)

        self.stdout.write("Создаю уведомления...")
        self._create_notifications(users)

        self.stdout.write(self.style.SUCCESS(
            "\nГотово! Тестовые данные загружены.\n"
            "\nПользователи (пароль для всех: test1234):\n"
            "  admin    / admin123  — Администратор\n"
            "  hr1      / test1234  — HR-специалист\n"
            "  hr2      / test1234  — HR-специалист\n"
            "  director / test1234  — Руководитель\n"
            "  ivanov   / test1234  — Кандидат (Иванов И.И.)\n"
            "  petrova  / test1234  — Кандидат (Петрова А.С.)\n"
            "  sidorov  / test1234  — Кандидат (Сидоров К.В.)\n"
            "  kuznets  / test1234  — Кандидат (Кузнецова М.Д.)\n"
            "  volkov   / test1234  — Кандидат (Волков Д.А.)\n"
        ))

    # ─── Пользователи ───

    def _create_users(self):
        def make(username, role, first, last, patron, email, phone):
            u, created = User.objects.get_or_create(username=username, defaults={
                "role": role,
                "first_name": first,
                "last_name": last,
                "patronymic": patron,
                "email": email,
                "phone": phone,
            })
            if created:
                u.set_password("test1234")
                u.save()
            return u

        admin = User.objects.filter(username="admin").first()
        if admin:
            admin.role = User.Role.ADMIN
            admin.first_name = "Админ"
            admin.last_name = "Системный"
            admin.save()

        hr1 = make("hr1", User.Role.HR, "Елена", "Смирнова", "Олеговна",
                    "smirnova@hr.local", "+7 (900) 111-22-33")
        hr2 = make("hr2", User.Role.HR, "Дмитрий", "Козлов", "Сергеевич",
                    "kozlov@hr.local", "+7 (900) 222-33-44")
        director = make("director", User.Role.DIRECTOR, "Алексей", "Морозов", "Петрович",
                        "morozov@hr.local", "+7 (900) 333-44-55")

        ivanov = make("ivanov", User.Role.CANDIDATE, "Игорь", "Иванов", "Иванович",
                      "ivanov@mail.ru", "+7 (912) 100-00-01")
        petrova = make("petrova", User.Role.CANDIDATE, "Анна", "Петрова", "Сергеевна",
                       "petrova@mail.ru", "+7 (912) 200-00-02")
        sidorov = make("sidorov", User.Role.CANDIDATE, "Кирилл", "Сидоров", "Валерьевич",
                       "sidorov@mail.ru", "+7 (912) 300-00-03")
        kuznets = make("kuznets", User.Role.CANDIDATE, "Мария", "Кузнецова", "Дмитриевна",
                       "kuznets@mail.ru", "+7 (912) 400-00-04")
        volkov = make("volkov", User.Role.CANDIDATE, "Денис", "Волков", "Андреевич",
                      "volkov@mail.ru", "+7 (912) 500-00-05")

        return {
            "admin": admin,
            "hr1": hr1, "hr2": hr2, "director": director,
            "ivanov": ivanov, "petrova": petrova, "sidorov": sidorov,
            "kuznets": kuznets, "volkov": volkov,
            "candidates": [ivanov, petrova, sidorov, kuznets, volkov],
        }

    # ─── Шаблоны опросов ───

    def _create_survey_templates(self, hr):
        templates = []

        t1, _ = SurveyTemplate.objects.get_or_create(
            title="Первичное интервью", defaults={"created_by": hr}
        )
        questions_t1 = [
            ("Расскажите о себе и вашем опыте работы.", 1, "text", []),
            ("Почему вы заинтересованы в этой позиции?", 2, "text", []),
            ("Какой у вас опыт работы в команде?", 3, "text", []),
            ("Готовы ли вы к переезду?", 4, "yes_no", []),
            ("Предпочтительный формат работы:", 5, "choice",
             ["Офис", "Удалёнка", "Гибрид"]),
        ]
        for text, order, qtype, opts in questions_t1:
            SurveyQuestion.objects.get_or_create(
                template=t1, order=order,
                defaults={"text": text, "question_type": qtype, "options": opts},
            )
        templates.append(t1)

        t2, _ = SurveyTemplate.objects.get_or_create(
            title="Техническое собеседование", defaults={"created_by": hr}
        )
        questions_t2 = [
            ("Какие языки программирования вы знаете?", 1, "text", []),
            ("Опишите свой самый сложный проект.", 2, "text", []),
            ("Знакомы ли вы с методологиями Agile/Scrum?", 3, "yes_no", []),
            ("Ваш уровень английского:", 4, "choice",
             ["A1-A2", "B1-B2", "C1-C2", "Native"]),
            ("Ожидаемый уровень зарплаты (руб./мес.):", 5, "text", []),
        ]
        for text, order, qtype, opts in questions_t2:
            SurveyQuestion.objects.get_or_create(
                template=t2, order=order,
                defaults={"text": text, "question_type": qtype, "options": opts},
            )
        templates.append(t2)

        t3, _ = SurveyTemplate.objects.get_or_create(
            title="Финальное собеседование с руководителем", defaults={"created_by": hr}
        )
        questions_t3 = [
            ("Какие ваши карьерные цели на ближайшие 3 года?", 1, "text", []),
            ("Что для вас важно в рабочей среде?", 2, "text", []),
            ("Когда вы готовы приступить к работе?", 3, "text", []),
        ]
        for text, order, qtype, opts in questions_t3:
            SurveyQuestion.objects.get_or_create(
                template=t3, order=order,
                defaults={"text": text, "question_type": qtype, "options": opts},
            )
        templates.append(t3)

        return templates

    # ─── Вакансии ───

    def _create_vacancies(self, users, templates):
        now = timezone.now()
        data = [
            ("Python-разработчик", "Разработка бэкенда на Django/FastAPI, REST API, интеграции.",
             "IT-отдел", "open", 180000, 250000, users["hr1"], now - timedelta(days=30)),
            ("Frontend-разработчик", "React/Vue, вёрстка, работа с API.",
             "IT-отдел", "open", 150000, 220000, users["hr1"], now - timedelta(days=25)),
            ("QA-инженер", "Ручное и автоматизированное тестирование, написание тест-кейсов.",
             "IT-отдел", "open", 120000, 170000, users["hr2"], now - timedelta(days=20)),
            ("Менеджер по продажам", "Работа с клиентами B2B, выполнение плана продаж.",
             "Отдел продаж", "open", 100000, 180000, users["hr2"], now - timedelta(days=15)),
            ("HR-менеджер", "Подбор персонала, onboarding, адаптация сотрудников.",
             "HR-отдел", "on_hold", 90000, 140000, users["hr1"], now - timedelta(days=45)),
            ("Бухгалтер", "Ведение бухгалтерского учёта, отчётность.",
             "Финансы", "closed", 80000, 120000, users["hr2"], now - timedelta(days=60)),
        ]

        vacancies = []
        for title, desc, dept, status, sal_from, sal_to, creator, created in data:
            v, _ = Vacancy.objects.get_or_create(title=title, defaults={
                "description": desc, "department": dept, "status": status,
                "salary_from": sal_from, "salary_to": sal_to,
                "created_by": creator,
            })
            if _:
                Vacancy.objects.filter(pk=v.pk).update(created_at=created)
                v.refresh_from_db()
            vacancies.append(v)

        stage_configs = [
            (vacancies[0], [
                ("Скрининг резюме", 1, "Проверка опыта и навыков", None),
                ("Первичное интервью", 2, "Общее знакомство", templates[0]),
                ("Техническое собеседование", 3, "Проверка знаний Python/Django", templates[1]),
                ("Финал с руководителем", 4, "Принятие решения", templates[2]),
            ]),
            (vacancies[1], [
                ("Скрининг резюме", 1, "Проверка портфолио", None),
                ("Первичное интервью", 2, "Знакомство", templates[0]),
                ("Тестовое задание", 3, "Вёрстка + React-компонент", None),
                ("Финал с руководителем", 4, "Принятие решения", templates[2]),
            ]),
            (vacancies[2], [
                ("Скрининг резюме", 1, "", None),
                ("Интервью", 2, "Проверка навыков тестирования", templates[0]),
                ("Финал", 3, "", templates[2]),
            ]),
            (vacancies[3], [
                ("Скрининг", 1, "", None),
                ("Собеседование", 2, "", templates[0]),
            ]),
        ]

        for vacancy, stages in stage_configs:
            for title, order, desc, tmpl in stages:
                InterviewStage.objects.get_or_create(
                    vacancy=vacancy, order=order,
                    defaults={"title": title, "description": desc, "survey_template": tmpl},
                )

        return vacancies

    # ─── Отклики и собеседования ───

    def _create_applications(self, users, vacancies, templates):
        now = timezone.now()
        candidates = users["candidates"]

        app_data = [
            (vacancies[0], candidates[0], "interview", 3, -20),
            (vacancies[0], candidates[1], "offer", 4, -18),
            (vacancies[0], candidates[2], "screening", 1, -10),
            (vacancies[1], candidates[1], "interview", 2, -15),
            (vacancies[1], candidates[3], "new", None, -5),
            (vacancies[2], candidates[4], "interview", 2, -12),
            (vacancies[2], candidates[0], "rejected", 1, -22),
            (vacancies[3], candidates[2], "hired", 2, -40),
            (vacancies[3], candidates[3], "screening", 1, -8),
            (vacancies[5], candidates[4], "hired", None, -55),
        ]

        for vacancy, candidate, status, stage_order, days_ago in app_data:
            stage = None
            if stage_order:
                stage = InterviewStage.objects.filter(
                    vacancy=vacancy, order=stage_order
                ).first()

            app, created = Application.objects.get_or_create(
                vacancy=vacancy, candidate=candidate,
                defaults={
                    "status": status,
                    "current_stage": stage,
                },
            )
            if created:
                Application.objects.filter(pk=app.pk).update(
                    applied_at=now + timedelta(days=days_ago)
                )
                app.refresh_from_db()

            if stage and status in ("interview", "offer", "hired"):
                completed_stages = InterviewStage.objects.filter(
                    vacancy=vacancy, order__lt=stage_order
                )
                for cs in completed_stages:
                    dt = now + timedelta(days=days_ago + cs.order * 3)
                    Interview.objects.get_or_create(
                        application=app, stage=cs,
                        defaults={
                            "scheduled_at": dt,
                            "status": Interview.Status.COMPLETED,
                            "notes": f"Этап «{cs.title}» пройден.",
                        },
                    )

                if status == "interview":
                    Interview.objects.get_or_create(
                        application=app, stage=stage,
                        defaults={
                            "scheduled_at": now + timedelta(days=2, hours=random.randint(9, 17)),
                            "status": Interview.Status.SCHEDULED,
                        },
                    )
                elif status == "offer":
                    Interview.objects.get_or_create(
                        application=app, stage=stage,
                        defaults={
                            "scheduled_at": now + timedelta(days=days_ago + stage_order * 3),
                            "status": Interview.Status.COMPLETED,
                            "notes": "Отлично! Кандидат принят на следующий этап.",
                        },
                    )

        # Completed survey for petrova (offer on vacancy 0)
        app_petrova = Application.objects.filter(
            vacancy=vacancies[0], candidate=candidates[1]
        ).first()
        if app_petrova:
            room = ChatRoom.objects.filter(candidate=candidates[1]).first()
            for iv in app_petrova.interviews.filter(survey__isnull=True):
                if iv.stage.survey_template:
                    survey = Survey.objects.create(
                        template=iv.stage.survey_template,
                        chat_room=room,
                        candidate=candidates[1],
                        status=Survey.Status.COMPLETED,
                        completed_at=iv.scheduled_at + timedelta(hours=1),
                    )
                    iv.survey = survey
                    iv.save()
                    for q in iv.stage.survey_template.questions.all():
                        answers_map = {
                            "text": "Мой опыт включает работу в нескольких IT-компаниях.",
                            "yes_no": "Да",
                            "choice": (q.options[0] if q.options else "Вариант 1"),
                        }
                        SurveyAnswer.objects.get_or_create(
                            survey=survey, question=q,
                            defaults={"answer_text": answers_map.get(q.question_type, "Ответ")},
                        )

    # ─── Документы ───

    def _create_documents(self, users):
        now = timezone.now()
        hr = users["hr1"]

        docs_data = [
            (users["ivanov"], "Резюме — Иванов И.И.", "Резюме на позицию Python-разработчик",
             Document.Status.APPROVED, "resume_ivanov.pdf", True),
            (users["ivanov"], "Согласие на обработку ПД", "Персональные данные",
             Document.Status.PENDING, "consent_ivanov.pdf", False),
            (users["petrova"], "Резюме — Петрова А.С.", "Резюме на позицию Frontend-разработчик",
             Document.Status.APPROVED, "resume_petrova.pdf", True),
            (users["petrova"], "Диплом", "Копия диплома о высшем образовании",
             Document.Status.APPROVED, "diploma_petrova.pdf", True),
            (users["sidorov"], "Резюме — Сидоров К.В.", "Резюме",
             Document.Status.DRAFT, "resume_sidorov.pdf", False),
            (users["kuznets"], "Резюме — Кузнецова М.Д.", "Резюме на позицию менеджер",
             Document.Status.REJECTED, "resume_kuznets.pdf", True),
            (users["volkov"], "Резюме — Волков Д.А.", "Резюме QA-инженер",
             Document.Status.APPROVED, "resume_volkov.pdf", True),
            (users["volkov"], "Рекомендательное письмо", "От предыдущего работодателя",
             Document.Status.PENDING, "recommendation_volkov.pdf", False),
        ]

        for candidate, title, desc, status, filename, has_approval in docs_data:
            doc, created = Document.objects.get_or_create(
                title=title, candidate=candidate,
                defaults={"description": desc, "status": status},
            )
            if created:
                content = f"[Тестовый файл: {title}]\n\nКандидат: {candidate.get_full_name()}\n"
                DocumentVersion.objects.create(
                    document=doc,
                    file=ContentFile(content.encode(), name=filename),
                    version_number=1,
                    uploaded_by=candidate,
                    comment="Первая загрузка",
                )

                if status == Document.Status.REJECTED:
                    DocumentApproval.objects.create(
                        document=doc, reviewer=hr,
                        decision=DocumentApproval.Decision.REJECTED,
                        comment="Резюме неполное, добавьте опыт работы.",
                        decided_at=now - timedelta(days=5),
                    )
                    content_v2 = content + "Дополнено: опыт работы\n"
                    DocumentVersion.objects.create(
                        document=doc,
                        file=ContentFile(content_v2.encode(), name=f"v2_{filename}"),
                        version_number=2,
                        uploaded_by=candidate,
                        comment="Дополненная версия с опытом работы",
                    )

                if has_approval and status == Document.Status.APPROVED:
                    DocumentApproval.objects.create(
                        document=doc, reviewer=hr,
                        decision=DocumentApproval.Decision.APPROVED,
                        comment="Всё в порядке.",
                        decided_at=now - timedelta(days=3),
                    )

    # ─── Чаты и сообщения ───

    def _create_chats(self, users, templates):
        now = timezone.now()
        hr1 = users["hr1"]
        hr2 = users["hr2"]

        chat_pairs = [
            (users["ivanov"], hr1),
            (users["petrova"], hr1),
            (users["sidorov"], hr2),
            (users["kuznets"], hr2),
            (users["volkov"], hr1),
        ]

        conversations = {
            "ivanov": [
                (hr1, "Здравствуйте, Игорь! Мы получили ваш отклик на вакансию Python-разработчик.", -5, 0),
                (users["ivanov"], "Здравствуйте! Да, очень заинтересован в этой позиции.", -5, 5),
                (hr1, "Отлично! Предлагаю назначить техническое собеседование. Вам удобно в среду в 15:00?", -5, 10),
                (users["ivanov"], "Да, среда в 15:00 подходит.", -5, 15),
                (hr1, "Замечательно, отправлю вам приглашение. Также прошу загрузить согласие на обработку ПД в раздел документов.", -5, 20),
                (users["ivanov"], "Хорошо, загружу сегодня.", -5, 25),
                (None, "Вам назначен опрос: «Первичное интервью». Пожалуйста, заполните его.", -4, 0),
                (users["ivanov"], "Спасибо, заполнил опрос.", -3, 30),
                (hr1, "Отлично, результаты получены. Ждём вас на собеседовании!", -3, 45),
            ],
            "petrova": [
                (hr1, "Добрый день, Анна! Рады вашему отклику на позицию Frontend-разработчик.", -10, 0),
                (users["petrova"], "Добрый день! Спасибо за ответ.", -10, 10),
                (hr1, "Ваше резюме нас впечатлило. Предлагаю пройти первичное интервью.", -10, 20),
                (users["petrova"], "С удовольствием! Когда можно?", -10, 30),
                (hr1, "Как насчёт пятницы в 11:00?", -10, 40),
                (users["petrova"], "Отлично, буду.", -10, 50),
                (hr1, "Вам также отправлен оффер на позицию Python-разработчик. Поздравляю!", -2, 0),
                (users["petrova"], "Ого, спасибо большое! Рассмотрю условия.", -2, 15),
            ],
            "sidorov": [
                (hr2, "Здравствуйте, Кирилл! Мы рассматриваем ваш отклик.", -3, 0),
                (users["sidorov"], "Здравствуйте! Буду ждать новостей.", -3, 20),
                (hr2, "Пожалуйста, загрузите резюме в раздел документов, если ещё не сделали.", -3, 30),
                (users["sidorov"], "Загружу сегодня, спасибо за напоминание.", -2, 0),
            ],
            "kuznets": [
                (hr2, "Здравствуйте, Мария! Спасибо за интерес к вакансии менеджера по продажам.", -7, 0),
                (users["kuznets"], "Здравствуйте! Очень хочу попробовать.", -7, 15),
                (hr2, "К сожалению, резюме неполное — нужно добавить опыт работы. Загрузите обновлённую версию.", -5, 0),
                (users["kuznets"], "Хорошо, обновлю.", -4, 0),
                (users["kuznets"], "Загрузила новую версию.", -3, 0),
                (hr2, "Спасибо! Рассмотрим и вернёмся с ответом.", -3, 15),
            ],
            "volkov": [
                (hr1, "Денис, добрый день! Ваш отклик на QA-инженера рассмотрен.", -8, 0),
                (users["volkov"], "Добрый день! Какие дальнейшие шаги?", -8, 30),
                (hr1, "Предлагаю пройти интервью. Удобно ли вам во вторник в 14:00?", -7, 0),
                (users["volkov"], "Да, вторник подходит.", -7, 15),
                (None, "Вам назначен опрос: «Первичное интервью». Пожалуйста, заполните его.", -6, 0),
                (users["volkov"], "Заполнил опрос.", -5, 0),
                (hr1, "Отлично! До встречи на собеседовании.", -5, 10),
            ],
        }

        for candidate, recruiter in chat_pairs:
            room, _ = ChatRoom.objects.get_or_create(
                candidate=candidate, recruiter=recruiter
            )
            key = candidate.username
            if key in conversations:
                for sender, text, day_offset, minute_offset in conversations[key]:
                    ts = now + timedelta(days=day_offset, minutes=minute_offset)
                    is_sys = sender is None
                    if not Message.objects.filter(room=room, text=text).exists():
                        Message.objects.create(
                            room=room,
                            sender=sender,
                            text=text,
                            is_system=is_sys,
                        )
                        Message.objects.filter(room=room, text=text).update(created_at=ts)

        # Survey sent in Ivanov's chat
        room_ivanov = ChatRoom.objects.filter(candidate=users["ivanov"]).first()
        if room_ivanov:
            survey, created = Survey.objects.get_or_create(
                template=templates[0],
                candidate=users["ivanov"],
                chat_room=room_ivanov,
                defaults={"status": Survey.Status.COMPLETED, "completed_at": now - timedelta(days=3)},
            )
            if created:
                for q in templates[0].questions.all():
                    answers = {
                        "text": "У меня 5 лет опыта в Python, работал в крупных проектах.",
                        "yes_no": "Нет",
                        "choice": q.options[0] if q.options else "Гибрид",
                    }
                    SurveyAnswer.objects.create(
                        survey=survey, question=q,
                        answer_text=answers.get(q.question_type, "Ответ"),
                    )

    # ─── Уведомления ───

    def _create_notifications(self, users):
        now = timezone.now()
        notifs = [
            (users["ivanov"], "Собеседование назначено",
             "Техническое собеседование по вакансии «Python-разработчик» назначено.",
             "/vacancies/", False),
            (users["ivanov"], "Документ согласован",
             "Ваше резюме было согласовано HR-специалистом.",
             "/documents/", True),
            (users["petrova"], "Поздравляем!",
             "Вам направлен оффер на позицию Python-разработчик.",
             "/vacancies/", False),
            (users["hr1"], "Новый отклик",
             "Кузнецова М.Д. откликнулась на вакансию «Менеджер по продажам».",
             "/vacancies/applications/", False),
            (users["hr1"], "Новый отклик",
             "Сидоров К.В. откликнулся на вакансию «Python-разработчик».",
             "/vacancies/applications/", True),
            (users["hr2"], "Документ на согласовании",
             "Волков Д.А. отправил рекомендательное письмо на согласование.",
             "/documents/", False),
            (users["kuznets"], "Документ отклонён",
             "Ваше резюме было отклонено. Пожалуйста, дополните его.",
             "/documents/", True),
            (users["volkov"], "Собеседование назначено",
             "Интервью по вакансии «QA-инженер» назначено на ближайший вторник.",
             "/vacancies/", False),
            (users["director"], "Еженедельная сводка",
             "На этой неделе: 3 новых отклика, 2 собеседования, 1 оффер.",
             "/analytics/", False),
        ]

        for user, title, message, link, is_read in notifs:
            if not Notification.objects.filter(user=user, title=title, message=message).exists():
                Notification.objects.create(
                    user=user, title=title, message=message,
                    link=link, is_read=is_read,
                )
