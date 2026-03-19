from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.contrib import messages

from .forms import LoginForm, ProfileForm


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = "accounts:login"


@login_required
def home_view(request):
    user = request.user
    if user.is_candidate:
        return redirect("vacancies:vacancy_list")
    if user.can_view_analytics:
        return redirect("analytics:dashboard")
    return redirect("vacancies:vacancy_list")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
