from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import manager_required
from .forms import ApprovalForm, DocumentUploadForm, NewVersionForm
from .models import Document, DocumentApproval, DocumentVersion


@login_required
def document_list(request):
    user = request.user
    if user.is_candidate:
        docs = Document.objects.filter(candidate=user)
    else:
        docs = Document.objects.all()

    status_filter = request.GET.get("status")
    if status_filter:
        docs = docs.filter(status=status_filter)

    return render(request, "documents/list.html", {
        "documents": docs,
        "status_filter": status_filter,
        "status_choices": Document.Status.choices,
    })


@login_required
def document_upload(request):
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.candidate = request.user
            doc.save()
            DocumentVersion.objects.create(
                document=doc,
                file=form.cleaned_data["file"],
                version_number=1,
                uploaded_by=request.user,
                comment=form.cleaned_data.get("comment", ""),
            )
            messages.success(request, "Документ загружен.")
            return redirect("documents:document_detail", pk=doc.pk)
    else:
        form = DocumentUploadForm()
    return render(request, "documents/upload.html", {"form": form})


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    user = request.user

    if user.is_candidate and doc.candidate != user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    versions = doc.versions.all()
    approvals = doc.approvals.all()
    new_version_form = None
    can_submit = False

    if user == doc.candidate:
        new_version_form = NewVersionForm()
        can_submit = doc.status in (Document.Status.DRAFT, Document.Status.REJECTED)

    if request.method == "POST":
        if "upload_version" in request.POST and user == doc.candidate:
            new_version_form = NewVersionForm(request.POST, request.FILES)
            if new_version_form.is_valid():
                last_ver = versions.first()
                new_num = (last_ver.version_number + 1) if last_ver else 1
                DocumentVersion.objects.create(
                    document=doc,
                    file=new_version_form.cleaned_data["file"],
                    version_number=new_num,
                    uploaded_by=user,
                    comment=new_version_form.cleaned_data.get("comment", ""),
                )
                messages.success(request, f"Версия {new_num} загружена.")
                return redirect("documents:document_detail", pk=pk)

        elif "submit_for_review" in request.POST and user == doc.candidate:
            doc.status = Document.Status.PENDING
            doc.save()
            messages.success(request, "Документ отправлен на согласование.")
            return redirect("documents:document_detail", pk=pk)

    return render(request, "documents/detail.html", {
        "doc": doc,
        "versions": versions,
        "approvals": approvals,
        "new_version_form": new_version_form,
        "can_submit": can_submit,
    })


@manager_required
def document_review(request, pk):
    doc = get_object_or_404(Document, pk=pk, status=Document.Status.PENDING)

    if request.method == "POST":
        form = ApprovalForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data["decision"]
            DocumentApproval.objects.create(
                document=doc,
                reviewer=request.user,
                decision=decision,
                comment=form.cleaned_data.get("comment", ""),
                decided_at=timezone.now(),
            )
            if decision == "approved":
                doc.status = Document.Status.APPROVED
            else:
                doc.status = Document.Status.REJECTED
            doc.save()
            messages.success(request, f"Документ {'согласован' if decision == 'approved' else 'отклонён'}.")
            return redirect("documents:document_detail", pk=pk)
    else:
        form = ApprovalForm()

    return render(request, "documents/review.html", {"doc": doc, "form": form})
