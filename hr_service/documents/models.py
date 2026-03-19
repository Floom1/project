from django.conf import settings
from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PENDING = "pending", "На согласовании"
        APPROVED = "approved", "Согласован"
        REJECTED = "rejected", "Отклонён"

    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Кандидат",
    )
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def current_version(self):
        return self.versions.order_by("-version_number").first()


class DocumentVersion(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="versions", verbose_name="Документ"
    )
    file = models.FileField("Файл", upload_to="documents/%Y/%m/")
    version_number = models.PositiveIntegerField("Версия")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Загрузил",
    )
    comment = models.TextField("Комментарий", blank=True)
    uploaded_at = models.DateTimeField("Загружен", auto_now_add=True)

    class Meta:
        verbose_name = "Версия документа"
        verbose_name_plural = "Версии документов"
        ordering = ["-version_number"]

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"


class DocumentApproval(models.Model):
    class Decision(models.TextChoices):
        PENDING = "pending", "Ожидает"
        APPROVED = "approved", "Согласовано"
        REJECTED = "rejected", "Отклонено"

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="approvals", verbose_name="Документ"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Рецензент",
    )
    decision = models.CharField(
        "Решение", max_length=20, choices=Decision.choices, default=Decision.PENDING
    )
    comment = models.TextField("Комментарий", blank=True)
    decided_at = models.DateTimeField("Дата решения", null=True, blank=True)

    class Meta:
        verbose_name = "Согласование"
        verbose_name_plural = "Согласования"

    def __str__(self):
        return f"{self.document.title} — {self.get_decision_display()}"
