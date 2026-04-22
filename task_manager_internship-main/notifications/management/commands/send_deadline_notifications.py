from django.core.management.base import BaseCommand

from notifications.utils import process_task_deadline_notifications


class Command(BaseCommand):
    help = "Create deadline-near and overdue notifications for assigned tasks."

    def handle(self, *args, **options):
        created_count = process_task_deadline_notifications()
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} notification(s)."))
