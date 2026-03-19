from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = BaseUserAdmin.list_filter + ("role",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("role", "patronymic", "phone")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Дополнительно", {"fields": ("role", "first_name", "last_name", "patronymic", "phone")}),
    )
