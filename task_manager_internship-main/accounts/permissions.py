from __future__ import annotations

from typing import Iterable

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


User = get_user_model()


ROLE_ACTIONS = {
    User.Role.MANAGER: {
        "view_all_tasks",
        "view_reports",
        "view_analytics",
        "view_team_tasks",
        "view_dashboard",
    },
    User.Role.TEAM_LEAD: {
        "create_task",
        "update_task",
        "assign_task",
        "view_team_tasks",
        "view_dashboard",
    },
    User.Role.EMPLOYEE: {
        "view_assigned_tasks",
        "start_task_timer",
        "stop_task_timer",
        "mark_task_completed",
        "view_dashboard",
    },
}


def get_user_role(user) -> str | None:
    if not getattr(user, "is_authenticated", False):
        return None
    if getattr(user, "is_superuser", False):
        return User.Role.MANAGER
    role = getattr(user, "role", None)
    valid_roles = {choice for choice, _label in User.Role.choices}
    return role if role in valid_roles else None


def has_permission(user, action: str) -> bool:
    role = get_user_role(user)
    if not role:
        return False
    return action in ROLE_ACTIONS.get(role, set())


def user_has_any_role(user, roles: Iterable[str]) -> bool:
    return get_user_role(user) in set(roles)


def require_action(user, action: str) -> None:
    if not has_permission(user, action):
        raise PermissionDenied("You do not have permission to perform this action.")


class RoleActionPermission(BasePermission):
    action_name: str | None = None

    def has_permission(self, request, view):
        action_name = getattr(view, "required_action", None) or self.action_name
        if not action_name:
            return False
        return has_permission(request.user, action_name)
