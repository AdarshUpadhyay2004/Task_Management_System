import secrets
import string

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from .decorators import manager_required
from .forms import EmployeeCreateForm, EmployeeUpdateForm, ProfileUpdateForm
from .permissions import get_user_role


User = get_user_model()


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AppLoginView(LoginView):
    template_name = "registration/login.html"


def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@login_required
def home(request):
    role = get_user_role(request.user)
    if role == User.Role.MANAGER:
        return redirect("manager_dashboard")
    if role == User.Role.TEAM_LEAD:
        return redirect("team_lead_dashboard")
    return redirect("task_list")


@manager_required
def employee_list(request):
    employees = User.objects.filter(is_superuser=False).order_by("role", "first_name", "last_name", "email")
    return render(request, "accounts/employee_list.html", {"employees": employees})


@manager_required
def employee_create(request):
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            password = _generate_password()
            user = form.save(commit=False)
            user.set_password(password)
            user.save()

            login_url = request.build_absolute_uri(reverse("login"))
            subject = "Your Task Manager Login"
            body = f"Login URL: {login_url}\nUsername/Email: {user.email}\nPassword: {password}\n"
            try:
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
                messages.success(request, f"User created. Credentials sent to {user.email}.")
            except Exception:
                messages.warning(request, f"User created, but email failed. Temporary password: {password}")
            return redirect("employee_list")
    else:
        form = EmployeeCreateForm()
    return render(request, "accounts/employee_create.html", {"form": form})


@manager_required
def employee_reset_password(request, user_id: int):
    user = get_object_or_404(User, pk=user_id, is_superuser=False)
    password = _generate_password()
    user.set_password(password)
    user.save(update_fields=["password"])

    login_url = request.build_absolute_uri(reverse("login"))
    subject = "Your Task Manager Password Reset"
    body = f"Login URL: {login_url}\nUsername/Email: {user.email}\nNew password: {password}\n"
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
        messages.success(request, f"Password reset. Credentials sent to {user.email}.")
    except Exception:
        messages.warning(request, f"Password reset, but email failed. Temporary password: {password}")
    return redirect("employee_list")


@manager_required
def employee_edit(request, user_id: int):
    employee = get_object_or_404(User, pk=user_id, is_superuser=False)
    if request.method == "POST":
        form = EmployeeUpdateForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated.")
            return redirect("employee_list")
    else:
        form = EmployeeUpdateForm(instance=employee)
    return render(request, "accounts/employee_edit.html", {"form": form, "employee": employee})


@login_required
def profile_settings(request):
    user = request.user
    profile_form = ProfileUpdateForm(instance=user)
    password_form = PasswordChangeForm(user)

    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile images updated.")
                return redirect("profile_settings")
        elif "change_password" in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated.")
                return redirect("profile_settings")

    return render(
        request,
        "accounts/profile_settings.html",
        {"profile_form": profile_form, "password_form": password_form},
    )


@manager_required
def admin_impersonate_employee(request, user_id: int):
    if request.method != "POST":
        return redirect("manager_dashboard")
    employee = get_object_or_404(User, pk=user_id, role=User.Role.EMPLOYEE)
    request.session["impersonator_id"] = request.user.pk
    login(request, employee, backend=settings.AUTHENTICATION_BACKENDS[0])
    messages.info(request, f"You are now logged in as {employee.email}.")
    return redirect("task_list")


@login_required
def stop_impersonation(request):
    admin_id = request.session.get("impersonator_id")
    if not admin_id:
        return redirect("home")
    admin_user = get_object_or_404(User, pk=admin_id)
    login(request, admin_user, backend=settings.AUTHENTICATION_BACKENDS[0])
    request.session.pop("impersonator_id", None)
    messages.success(request, "Returned to manager account.")
    return redirect("manager_dashboard")


# Create your views here.
