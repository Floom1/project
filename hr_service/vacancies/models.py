from django.conf import settings
from django.db import models


class Vacancy(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Открыта"
        ON_HOLD = "on_hold", "Приостановлена"
        CLOSED = "closed", "Закрыта"

    title = models.CharField("Должность", max_length=255)
    description = models.TextField("Описание")
    department = models.CharField("Отдел", max_length=255)
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.OPEN
    )
    salary_from = models.PositiveIntegerField("Зарплата от", null=True, blank=True)
    salary_to = models.PositiveIntegerField("Зарплата до", null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Создал",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    closed_at = models.DateTimeField("Закрыта", null=True, blank=True)

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class InterviewStage(models.Model):
    vacancy = models.ForeignKey(
        Vacancy, on_delete=models.CASCADE, related_name="stages", verbose_name="Вакансия"
    )
    title = models.CharField("Название этапа", max_length=255)
    order = models.PositiveIntegerField("Порядок", default=0)
    description = models.TextField("Описание", blank=True)
    survey_template = models.ForeignKey(
        "chat.SurveyTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Шаблон опроса",
    )

    class Meta:
        verbose_name = "Этап собеседования"
        verbose_name_plural = "Этапы собеседований"
        ordering = ["order"]

    def __str__(self):
        return f"{self.vacancy.title} — {self.title}"


class Application(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        SCREENING = "screening", "Скрининг"
        INTERVIEW = "interview", "Собеседование"
        OFFER = "offer", "Оффер"
        HIRED = "hired", "Нанят"
        REJECTED = "rejected", "Отклонён"

    vacancy = models.ForeignKey(
        Vacancy, on_delete=models.CASCADE, related_name="applications", verbose_name="Вакансия"
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="Кандидат",
    )
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.NEW
    )
    current_stage = models.ForeignKey(
        InterviewStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Текущий этап",
    )
    applied_at = models.DateTimeField("Дата отклика", auto_now_add=True)

    class Meta:
        verbose_name = "Отклик"
        verbose_name_plural = "Отклики"
        ordering = ["-applied_at"]
        unique_together = ("vacancy", "candidate")

    def __str__(self):
        return f"{self.candidate} → {self.vacancy.title}"


class Interview(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Запланировано"
        COMPLETED = "completed", "Завершено"
        CANCELLED = "cancelled", "Отменено"

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="interviews", verbose_name="Отклик"
    )
    stage = models.ForeignKey(
        InterviewStage, on_delete=models.CASCADE, verbose_name="Этап"
    )
    scheduled_at = models.DateTimeField("Дата и время")
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    notes = models.TextField("Заметки", blank=True)
    survey = models.ForeignKey(
        "chat.Survey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Опрос",
    )

    class Meta:
        verbose_name = "Собеседование"
        verbose_name_plural = "Собеседования"
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"{self.application.candidate} — {self.stage.title} ({self.scheduled_at:%d.%m.%Y %H:%M})"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Пользователь",
    )
    title = models.CharField("Заголовок", max_length=255)
    message = models.TextField("Сообщение")
    link = models.CharField("Ссылка", max_length=500, blank=True)
    is_read = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
