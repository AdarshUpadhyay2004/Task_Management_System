from django.apps import AppConfig


class PresenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "presence"

    def ready(self):
        from . import signals  # noqa: F401
