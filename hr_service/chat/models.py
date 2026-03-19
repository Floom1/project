from django.conf import settings
from django.db import models


class ChatRoom(models.Model):
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_chats",
        verbose_name="Кандидат",
    )
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter_chats",
        verbose_name="Рекрутер",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        unique_together = ("candidate", "recruiter")

    def __str__(self):
        return f"Чат: {self.candidate} — {self.recruiter}"

    @property
    def last_message(self):
        return self.messages.order_by("-created_at").first()


class Message(models.Model):
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages", verbose_name="Чат"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Отправитель",
    )
    text = models.TextField("Текст")
    created_at = models.DateTimeField("Отправлено", auto_now_add=True)
    is_system = models.BooleanField("Системное", default=False)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["created_at"]

    def __str__(self):
        sender_name = self.sender or "Система"
        return f"{sender_name}: {self.text[:50]}"


class SurveyTemplate(models.Model):
    title = models.CharField("Название", max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Шаблон опроса"
        verbose_name_plural = "Шаблоны опросов"

    def __str__(self):
        return self.title


class SurveyQuestion(models.Model):
    class QuestionType(models.TextChoices):
        TEXT = "text", "Текст"
        CHOICE = "choice", "Выбор"
        YES_NO = "yes_no", "Да/Нет"

    template = models.ForeignKey(
        SurveyTemplate,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Шаблон",
    )
    text = models.TextField("Вопрос")
    order = models.PositiveIntegerField("Порядок", default=0)
    question_type = models.CharField(
        "Тип", max_length=20, choices=QuestionType.choices, default=QuestionType.TEXT
    )
    options = models.JSONField("Варианты", default=list, blank=True)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["order"]

    def __str__(self):
        return f"{self.template.title} — Q{self.order}"


class Survey(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        IN_PROGRESS = "in_progress", "В процессе"
        COMPLETED = "completed", "Завершён"

    template = models.ForeignKey(
        SurveyTemplate, on_delete=models.CASCADE, verbose_name="Шаблон"
    )
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Чат",
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Кандидат",
    )
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    started_at = models.DateTimeField("Начат", auto_now_add=True)
    completed_at = models.DateTimeField("Завершён", null=True, blank=True)

    class Meta:
        verbose_name = "Опрос"
        verbose_name_plural = "Опросы"

    def __str__(self):
        return f"{self.template.title} — {self.candidate}"


class SurveyAnswer(models.Model):
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="answers", verbose_name="Опрос"
    )
    question = models.ForeignKey(
        SurveyQuestion, on_delete=models.CASCADE, verbose_name="Вопрос"
    )
    answer_text = models.TextField("Ответ")

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"Ответ на {self.question}"
