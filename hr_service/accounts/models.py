from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CANDIDATE = "candidate", "Кандидат"
        HR = "hr", "HR-специалист"
        DIRECTOR = "director", "Руководитель"
        ADMIN = "admin", "Администратор"

    role = models.CharField(
        "Роль", max_length=20, choices=Role.choices, default=Role.CANDIDATE
    )
    patronymic = models.CharField("Отчество", max_length=150, blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_candidate(self):
        return self.role == self.Role.CANDIDATE

    @property
    def is_hr(self):
        return self.role == self.Role.HR

    @property
    def is_director(self):
        return self.role == self.Role.DIRECTOR

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def can_manage(self):
        return self.role in (self.Role.HR, self.Role.DIRECTOR, self.Role.ADMIN)

    @property
    def can_view_analytics(self):
        return self.role in (self.Role.DIRECTOR, self.Role.ADMIN)
