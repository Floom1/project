from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from documents.forms import ApprovalForm, DocumentUploadForm, NewVersionForm
from documents.models import Document, DocumentApproval, DocumentVersion
from tests.factories import (
    DEFAULT_PASSWORD,
    create_document,
    create_document_version,
    create_user,
)


class DocumentModelTests(TestCase):
    def setUp(self):
        self.candidate = create_user("doc_candidate", role=User.Role.CANDIDATE)

    def test_current_version_returns_latest_version(self):
        document = create_document(self.candidate, title="Resume")
        create_document_version(document, self.candidate, version_number=1)
        latest = create_document_version(document, self.candidate, version_number=2)

        self.assertEqual(document.current_version, latest)

    def test_string_representations(self):
        document = create_document(self.candidate, title="CV")
        version = create_document_version(document, self.candidate, version_number=3)
        approval = DocumentApproval.objects.create(
            document=document,
            reviewer=self.candidate,
            decision=DocumentApproval.Decision.APPROVED,
        )

        self.assertEqual(str(document), "CV")
        self.assertEqual(str(version), "CV v3")
        self.assertIn("Согласовано", str(approval))


class DocumentFormTests(TestCase):
    def test_document_upload_form_valid(self):
        form = DocumentUploadForm(
            data={"title": "Test", "description": "Desc", "comment": "First version"},
            files={
                "file": SimpleUploadedFile("doc.txt", b"hello", content_type="text/plain")
            },
        )
        self.assertTrue(form.is_valid())

    def test_document_upload_form_invalid_without_file(self):
        form = DocumentUploadForm(data={"title": "Test", "description": "Desc"})
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_new_version_form_invalid_without_file(self):
        form = NewVersionForm(data={"comment": "next"})
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_approval_form_accepts_known_decision(self):
        form = ApprovalForm(data={"decision": "approved", "comment": "ok"})
        self.assertTrue(form.is_valid())

    def test_approval_form_rejects_unknown_decision(self):
        form = ApprovalForm(data={"decision": "maybe", "comment": "?"})
        self.assertFalse(form.is_valid())
        self.assertIn("decision", form.errors)


class DocumentViewTests(TestCase):
    def setUp(self):
        self.candidate = create_user("candidate_docs", role=User.Role.CANDIDATE)
        self.other_candidate = create_user("candidate_other", role=User.Role.CANDIDATE)
        self.hr = create_user("hr_docs", role=User.Role.HR)
        self.document = create_document(self.candidate, title="Resume", status=Document.Status.DRAFT)
        create_document_version(self.document, self.candidate, version_number=1)
        self.other_document = create_document(
            self.other_candidate,
            title="Other Resume",
            status=Document.Status.PENDING,
        )
        create_document_version(self.other_document, self.other_candidate, version_number=1)

    def test_candidate_sees_only_own_documents(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("documents:document_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resume")
        self.assertNotContains(response, "Other Resume")

    def test_manager_sees_all_documents(self):
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("documents:document_list"))

        self.assertContains(response, "Resume")
        self.assertContains(response, "Other Resume")

    def test_document_list_filters_by_status(self):
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("documents:document_list"), {"status": Document.Status.PENDING})

        self.assertNotContains(response, "Resume")
        self.assertContains(response, "Other Resume")

    def test_upload_creates_document_and_initial_version(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("documents:document_upload"),
            {
                "title": "Passport",
                "description": "Passport scan",
                "comment": "Initial",
                "file": SimpleUploadedFile("passport.txt", b"scan", content_type="text/plain"),
            },
        )

        created = Document.objects.get(title="Passport")
        self.assertRedirects(response, reverse("documents:document_detail", kwargs={"pk": created.pk}))
        self.assertEqual(created.candidate, self.candidate)
        self.assertEqual(created.versions.count(), 1)
        self.assertEqual(created.current_version.version_number, 1)

    def test_candidate_cannot_open_foreign_document_detail(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.get(
            reverse("documents:document_detail", kwargs={"pk": self.other_document.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_upload_new_version_increments_version_number(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("documents:document_detail", kwargs={"pk": self.document.pk}),
            {
                "upload_version": "1",
                "comment": "Updated",
                "file": SimpleUploadedFile("resume_v2.txt", b"updated", content_type="text/plain"),
            },
        )
        self.document.refresh_from_db()

        self.assertRedirects(response, reverse("documents:document_detail", kwargs={"pk": self.document.pk}))
        self.assertEqual(self.document.versions.count(), 2)
        self.assertEqual(self.document.current_version.version_number, 2)

    def test_candidate_can_submit_document_for_review(self):
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("documents:document_detail", kwargs={"pk": self.document.pk}),
            {"submit_for_review": "1"},
        )
        self.document.refresh_from_db()

        self.assertRedirects(response, reverse("documents:document_detail", kwargs={"pk": self.document.pk}))
        self.assertEqual(self.document.status, Document.Status.PENDING)

    def test_hr_can_approve_pending_document(self):
        self.other_document.status = Document.Status.PENDING
        self.other_document.save()
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("documents:document_review", kwargs={"pk": self.other_document.pk}),
            {"decision": "approved", "comment": "Looks good"},
        )
        self.other_document.refresh_from_db()

        self.assertRedirects(
            response,
            reverse("documents:document_detail", kwargs={"pk": self.other_document.pk}),
        )
        self.assertEqual(self.other_document.status, Document.Status.APPROVED)
        approval = self.other_document.approvals.get()
        self.assertEqual(approval.reviewer, self.hr)
        self.assertEqual(approval.decision, DocumentApproval.Decision.APPROVED)
        self.assertIsNotNone(approval.decided_at)

    def test_hr_can_reject_pending_document(self):
        self.other_document.status = Document.Status.PENDING
        self.other_document.save()
        self.client.login(username=self.hr.username, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("documents:document_review", kwargs={"pk": self.other_document.pk}),
            {"decision": "rejected", "comment": "Need changes"},
        )
        self.other_document.refresh_from_db()

        self.assertEqual(self.other_document.status, Document.Status.REJECTED)
        self.assertRedirects(
            response,
            reverse("documents:document_detail", kwargs={"pk": self.other_document.pk}),
        )

    def test_candidate_cannot_review_document(self):
        self.other_document.status = Document.Status.PENDING
        self.other_document.save()
        self.client.login(username=self.candidate.username, password=DEFAULT_PASSWORD)
        response = self.client.get(
            reverse("documents:document_review", kwargs={"pk": self.other_document.pk})
        )
        self.assertEqual(response.status_code, 403)
