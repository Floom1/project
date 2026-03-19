from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q

from accounts.decorators import manager_required
from chat.models import ChatRoom, Message, Survey, SurveyTemplate
from .forms import (
    ApplicationStatusForm, InterviewStageForm,
    ScheduleInterviewForm, VacancyForm,
)
from .models import Application, Interview, InterviewStage, Notification, Vacancy


@login_required
def vacancy_list(request):
    vacancies = Vacancy.objects.all()
    status_filter = request.GET.get("status")
    if status_filter:
        vacancies = vacancies.filter(status=status_filter)

    if request.user.is_candidate:
        vacancies = vacancies.filter(status=Vacancy.Status.OPEN)

    return render(request, "vacancies/list.html", {
        "vacancies": vacancies,
        "status_filter": status_filter,
        "status_choices": Vacancy.Status.choices,
    })


@login_required
def vacancy_detail(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    stages = vacancy.stages.all()
    user = request.user

    already_applied = False
    application = None
    if user.is_candidate:
        application = Application.objects.filter(vacancy=vacancy, candidate=user).first()
        already_applied = application is not None

    applications = None
    if user.can_manage:
        applications = vacancy.applications.select_related("candidate", "current_stage").all()

    return render(request, "vacancies/detail.html", {
        "vacancy": vacancy,
        "stages": stages,
        "already_applied": already_applied,
        "application": application,
        "applications": applications,
    })


@login_required
def vacancy_apply(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk, status=Vacancy.Status.OPEN)
    user = request.user

    if not user.is_candidate:
        raise PermissionDenied

    _, created = Application.objects.get_or_create(vacancy=vacancy, candidate=user)
    if created:
        messages.success(request, "Отклик отправлен!")
        for hr in vacancy.created_by.__class__.objects.filter(
            role__in=["hr", "director", "admin"]
        ):
            Notification.objects.create(
                user=hr,
                title="Новый отклик",
                message=f"{user} откликнулся на вакансию «{vacancy.title}»",
                link=f"/vacancies/{vacancy.pk}/",
            )
    else:
        messages.info(request, "Вы уже откликнулись на эту вакансию.")

    return redirect("vacancies:vacancy_detail", pk=pk)


@manager_required
def vacancy_create(request):
    if request.method == "POST":
        form = VacancyForm(request.POST)
        if form.is_valid():
            v = form.save(commit=False)
            v.created_by = request.user
            v.save()
            messages.success(request, "Вакансия создана.")
            return redirect("vacancies:vacancy_detail", pk=v.pk)
    else:
        form = VacancyForm()
    return render(request, "vacancies/vacancy_form.html", {"form": form, "is_new": True})


@manager_required
def vacancy_edit(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    if request.method == "POST":
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            form.save()
            messages.success(request, "Вакансия обновлена.")
            return redirect("vacancies:vacancy_detail", pk=pk)
    else:
        form = VacancyForm(instance=vacancy)
    return render(request, "vacancies/vacancy_form.html", {"form": form, "vacancy": vacancy, "is_new": False})


@manager_required
def stage_add(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    if request.method == "POST":
        form = InterviewStageForm(request.POST)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.vacancy = vacancy
            stage.save()
            messages.success(request, "Этап добавлен.")
            return redirect("vacancies:vacancy_detail", pk=pk)
    else:
        form = InterviewStageForm()
    return render(request, "vacancies/stage_form.html", {"form": form, "vacancy": vacancy})


@manager_required
def application_list(request):
    apps = Application.objects.select_related("vacancy", "candidate", "current_stage").all()
    status_filter = request.GET.get("status")
    if status_filter:
        apps = apps.filter(status=status_filter)
    return render(request, "vacancies/application_list.html", {
        "applications": apps,
        "status_filter": status_filter,
        "status_choices": Application.Status.choices,
    })


@manager_required
def application_detail(request, pk):
    app = get_object_or_404(
        Application.objects.select_related("vacancy", "candidate", "current_stage"), pk=pk
    )
    interviews = app.interviews.select_related("stage").all()
    stages = app.vacancy.stages.all()

    status_form = ApplicationStatusForm(instance=app)
    schedule_form = ScheduleInterviewForm()

    if request.method == "POST":
        if "update_status" in request.POST:
            status_form = ApplicationStatusForm(request.POST, instance=app)
            if status_form.is_valid():
                status_form.save()
                Notification.objects.create(
                    user=app.candidate,
                    title="Статус отклика обновлён",
                    message=f"Ваш отклик на «{app.vacancy.title}» теперь: {app.get_status_display()}",
                    link=f"/vacancies/{app.vacancy.pk}/",
                )
                messages.success(request, "Статус обновлён.")
                return redirect("vacancies:application_detail", pk=pk)

        elif "schedule_interview" in request.POST:
            schedule_form = ScheduleInterviewForm(request.POST)
            stage_id = request.POST.get("stage_id")
            stage = get_object_or_404(InterviewStage, pk=stage_id, vacancy=app.vacancy)
            if schedule_form.is_valid():
                interview = schedule_form.save(commit=False)
                interview.application = app
                interview.stage = stage
                interview.save()
                app.current_stage = stage
                app.status = Application.Status.INTERVIEW
                app.save()

                if stage.survey_template:
                    room = ChatRoom.objects.filter(candidate=app.candidate).first()
                    survey = Survey.objects.create(
                        template=stage.survey_template,
                        chat_room=room,
                        candidate=app.candidate,
                        status=Survey.Status.PENDING,
                    )
                    interview.survey = survey
                    interview.save()
                    if room:
                        Message.objects.create(
                            room=room, sender=None,
                            text=f"Вам назначен опрос «{stage.survey_template.title}» к этапу «{stage.title}».",
                            is_system=True,
                        )

                Notification.objects.create(
                    user=app.candidate,
                    title="Собеседование назначено",
                    message=f"Этап «{stage.title}» по вакансии «{app.vacancy.title}» назначен на {interview.scheduled_at:%d.%m.%Y %H:%M}.",
                    link=f"/vacancies/applications/{app.pk}/",
                )
                messages.success(request, "Собеседование назначено.")
                return redirect("vacancies:application_detail", pk=pk)

    return render(request, "vacancies/application_detail.html", {
        "app": app,
        "interviews": interviews,
        "stages": stages,
        "status_form": status_form,
        "schedule_form": schedule_form,
    })


@manager_required
def interview_list(request):
    interviews = Interview.objects.select_related(
        "application__candidate", "application__vacancy", "stage"
    ).all()
    status_filter = request.GET.get("status")
    if status_filter:
        interviews = interviews.filter(status=status_filter)
    return render(request, "vacancies/interview_list.html", {
        "interviews": interviews,
        "status_filter": status_filter,
        "status_choices": Interview.Status.choices,
    })


@manager_required
def interview_complete(request, pk):
    interview = get_object_or_404(Interview, pk=pk)
    if request.method == "POST":
        interview.status = Interview.Status.COMPLETED
        interview.notes = request.POST.get("notes", "")
        interview.save()
        messages.success(request, "Собеседование завершено.")
    return redirect("vacancies:application_detail", pk=interview.application.pk)


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    unread = notifications.filter(is_read=False)
    unread.update(is_read=True)
    return render(request, "notifications/list.html", {"notifications": notifications})


@login_required
def unread_notification_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"count": count})
