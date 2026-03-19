from django.contrib import admin

from .models import (
    ChatRoom, Message, Survey, SurveyAnswer,
    SurveyQuestion, SurveyTemplate,
)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("candidate", "recruiter", "created_at")
    inlines = [MessageInline]


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1


@admin.register(SurveyTemplate)
class SurveyTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "created_at")
    inlines = [SurveyQuestionInline]


class SurveyAnswerInline(admin.TabularInline):
    model = SurveyAnswer
    extra = 0


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("template", "candidate", "status", "started_at")
    inlines = [SurveyAnswerInline]
