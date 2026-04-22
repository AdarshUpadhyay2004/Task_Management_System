from django.contrib.auth.decorators import user_passes_test

from .permissions import get_user_role, has_permission


def role_required(*roles):
    return user_passes_test(lambda u: u.is_authenticated and get_user_role(u) in roles)


def action_required(action):
    return user_passes_test(lambda u: u.is_authenticated and has_permission(u, action))


def manager_required(view_func):
    return role_required("MANAGER")(view_func)


def team_lead_required(view_func):
    return role_required("TEAM_LEAD")(view_func)


def employee_required(view_func):
    return role_required("EMPLOYEE")(view_func)
