from __future__ import annotations

from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from accounts.models import User
from chat.models import ChatRoom, Message, SurveyTemplate, SurveyQuestion
from documents.models import Document, DocumentVersion
from vacancies.models import Vacancy, InterviewStage, Application, Interview, Notification


DEFAULT_PASSWORD = "testpass123"


def create_user(
    username: str,
    role: str = User.Role.CANDIDATE,
    password: str = DEFAULT_PASSWORD,
    **kwargs,
):
    defaults = {
        "email": f"{username}@example.com",
        "first_name": kwargs.pop("first_name", username.capitalize()),
        "last_name": kwargs.pop("last_name", "User"),
        "role": role,
    }
    defaults.update(kwargs)
    user = User.objects.create_user(username=username, password=password, **defaults)
    return user


def create_document(candidate: User, title: str = "Документ", status: str = Document.Status.DRAFT):
    return Document.objects.create(
        title=title,
        description=f"Описание для {title}",
        candidate=candidate,
        status=status,
    )


def create_document_version(document: Document, uploaded_by: User, version_number: int = 1):
    return DocumentVersion.objects.create(
        document=document,
        file=SimpleUploadedFile(
            f"doc_v{version_number}.txt",
            f"version {version_number}".encode(),
            content_type="text/plain",
        ),
        version_number=version_number,
        uploaded_by=uploaded_by,
        comment=f"Комментарий {version_number}",
    )


def create_chat_room(candidate: User, recruiter: User):
    return ChatRoom.objects.create(candidate=candidate, recruiter=recruiter)


def create_message(room: ChatRoom, sender: User | None, text: str = "Сообщение", **kwargs):
    return Message.objects.create(room=room, sender=sender, text=text, **kwargs)


def create_survey_template(created_by: User, title: str = "Шаблон опроса"):
    return SurveyTemplate.objects.create(title=title, created_by=created_by)


def create_survey_question(
    template: SurveyTemplate,
    order: int = 1,
    question_type: str = SurveyQuestion.QuestionType.TEXT,
    text: str | None = None,
    options: list[str] | None = None,
):
    return SurveyQuestion.objects.create(
        template=template,
        order=order,
        text=text or f"Вопрос {order}",
        question_type=question_type,
        options=options or [],
    )


def create_vacancy(created_by: User, title: str = "Python Developer", status: str = Vacancy.Status.OPEN):
    return Vacancy.objects.create(
        title=title,
        description=f"Описание {title}",
        department="IT",
        status=status,
        salary_from=100000,
        salary_to=200000,
        created_by=created_by,
    )


def create_stage(vacancy: Vacancy, order: int = 1, title: str | None = None, survey_template=None):
    return InterviewStage.objects.create(
        vacancy=vacancy,
        title=title or f"Этап {order}",
        order=order,
        description=f"Описание этапа {order}",
        survey_template=survey_template,
    )


def create_application(
    vacancy: Vacancy,
    candidate: User,
    status: str = Application.Status.NEW,
    current_stage: InterviewStage | None = None,
):
    return Application.objects.create(
        vacancy=vacancy,
        candidate=candidate,
        status=status,
        current_stage=current_stage,
    )


def create_interview(
    application: Application,
    stage: InterviewStage,
    status: str = Interview.Status.SCHEDULED,
    scheduled_at=None,
):
    return Interview.objects.create(
        application=application,
        stage=stage,
        scheduled_at=scheduled_at or timezone.now() + timedelta(days=1),
        status=status,
    )


def create_notification(user: User, title: str = "Уведомление", is_read: bool = False):
    return Notification.objects.create(
        user=user,
        title=title,
        message=f"Сообщение: {title}",
        link="/",
        is_read=is_read,
    )
