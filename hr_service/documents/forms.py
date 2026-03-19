from django import forms

from .models import Document, DocumentVersion, DocumentApproval


class DocumentUploadForm(forms.ModelForm):
    file = forms.FileField(label="Файл", widget=forms.ClearableFileInput(attrs={"class": "form-control"}))
    comment = forms.CharField(
        label="Комментарий к версии", required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    class Meta:
        model = Document
        fields = ("title", "description")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class NewVersionForm(forms.Form):
    file = forms.FileField(label="Файл", widget=forms.ClearableFileInput(attrs={"class": "form-control"}))
    comment = forms.CharField(
        label="Комментарий", required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )


class ApprovalForm(forms.Form):
    DECISIONS = [("approved", "Согласовать"), ("rejected", "Отклонить")]
    decision = forms.ChoiceField(
        label="Решение", choices=DECISIONS,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    comment = forms.CharField(
        label="Комментарий", required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
