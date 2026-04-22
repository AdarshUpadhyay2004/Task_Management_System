from __future__ import annotations

from threading import local


_audit_state = local()


def set_current_user(user):
    _audit_state.user = user


def get_current_user():
    return getattr(_audit_state, "user", None)


class CurrentUserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            set_current_user(None)
