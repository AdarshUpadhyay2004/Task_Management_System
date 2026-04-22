from django.urls import path
from . import views


urlpatterns = [
    path("login/", views.AppLoginView.as_view(), name="login"),
    path("profile/settings/", views.profile_settings, name="profile_settings"),
    path("impersonate/<int:user_id>/", views.admin_impersonate_employee, name="admin_impersonate_employee"),
    path("impersonate/stop/", views.stop_impersonation, name="stop_impersonation"),
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/new/", views.employee_create, name="employee_create"),
    path("employees/<int:user_id>/edit/", views.employee_edit, name="employee_edit"),
    path("employees/<int:user_id>/reset-password/", views.employee_reset_password, name="employee_reset_password"),
]
