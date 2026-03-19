from django.contrib import admin

from .models import Document, DocumentApproval, DocumentVersion


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0


class DocumentApprovalInline(admin.TabularInline):
    model = DocumentApproval
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "candidate", "status", "created_at")
    list_filter = ("status",)
    inlines = [DocumentVersionInline, DocumentApprovalInline]


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "uploaded_by", "uploaded_at")


@admin.register(DocumentApproval)
class DocumentApprovalAdmin(admin.ModelAdmin):
    list_display = ("document", "reviewer", "decision", "decided_at")
