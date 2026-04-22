from .permissions import get_user_role


class CurrentRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_role = get_user_role(getattr(request, "user", None))
        return self.get_response(request)
