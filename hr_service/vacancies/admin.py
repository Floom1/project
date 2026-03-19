from django.contrib import admin

from .models import (
    Application, Interview, InterviewStage,
    Notification, Vacancy,
)


class InterviewStageInline(admin.TabularInline):
    model = InterviewStage
    extra = 1


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "status", "created_at")
    list_filter = ("status", "department")
    inlines = [InterviewStageInline]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "vacancy", "status", "applied_at")
    list_filter = ("status",)


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("application", "stage", "scheduled_at", "status")
    list_filter = ("status",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_read", "created_at")
    list_filter = ("is_read",)
