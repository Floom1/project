from django import forms

from chat.models import SurveyTemplate
from .models import Vacancy, InterviewStage, Interview, Application


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ("title", "description", "department", "status", "salary_from", "salary_to")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "salary_from": forms.NumberInput(attrs={"class": "form-control"}),
            "salary_to": forms.NumberInput(attrs={"class": "form-control"}),
        }


class InterviewStageForm(forms.ModelForm):
    class Meta:
        model = InterviewStage
        fields = ("title", "order", "description", "survey_template")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "survey_template": forms.Select(attrs={"class": "form-select"}),
        }


class ScheduleInterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ("scheduled_at",)
        widgets = {
            "scheduled_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ("status",)
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
        }
