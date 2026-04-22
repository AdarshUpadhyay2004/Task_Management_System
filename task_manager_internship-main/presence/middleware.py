from django.utils import timezone

from .models import UserProfile


class UpdateLastSeenMiddleware:
    """
    Store the authenticated user's latest HTTP activity time.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"last_seen": timezone.now()},
            )

        return response
