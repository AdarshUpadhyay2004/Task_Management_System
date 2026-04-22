from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from tasks.models import Task, TaskSession
from .utils import detect_language, translate_to_english, translate_to_hindi


def _format_task_list(tasks, empty_message: str) -> str:
    if not tasks:
        return empty_message
    return "\n".join(f"- {task.title} ({task.get_status_display()})" for task in tasks)


def _format_duration(total_seconds: int) -> str:
    duration = timedelta(seconds=total_seconds)
    hours, remainder = divmod(int(duration.total_seconds()), 3600)
    minutes = remainder // 60
    return f"{hours} hour(s) and {minutes} minute(s)"


def _build_english_response(user, message: str) -> str:
    """
    Core chatbot logic in English.
    """
    text = message.lower().strip()

    if not text:
        return "Please type a message so I can help."

    assigned_tasks = Task.objects.filter(assigned_to=user).order_by("-created_at")

    if "high priority" in text:
        tasks = list(assigned_tasks.filter(priority=Task.Priority.HIGH)[:10])
        return _format_task_list(tasks, "You do not have any high priority tasks.")

    if "today tasks" in text or "today task" in text:
        today = timezone.localdate()
        tasks = list(assigned_tasks.filter(created_at__date=today)[:10])
        return _format_task_list(tasks, "You do not have any tasks created today.")

    if "pending" in text:
        tasks = list(assigned_tasks.exclude(status=Task.Status.DONE)[:10])
        return _format_task_list(tasks, "You do not have any pending tasks.")

    if "completed" in text:
        tasks = list(assigned_tasks.filter(status=Task.Status.DONE)[:10])
        return _format_task_list(tasks, "You do not have any completed tasks.")

    if "assigned to me" in text or "my tasks" in text:
        tasks = list(assigned_tasks[:10])
        return _format_task_list(tasks, "You do not have any tasks assigned to you.")

    if "time" in text or "hours" in text:
        today = timezone.localdate()
        total_seconds = (
            TaskSession.objects.filter(employee=user, started_at__date=today)
            .aggregate(total=Sum("duration_seconds"))["total"]
            or 0
        )
        return f"You worked {_format_duration(total_seconds)} today."

    return "Sorry, I didn't understand. Try asking about pending tasks, completed tasks, hours, or assigned tasks."


def analyze_message(user, message: str) -> str:
    """
    Detect language, translate Hindi/Hinglish to English, process the request,
    and return the response in the same language as the user input.
    """
    original_message = (message or "").strip()
    original_language = detect_language(original_message)

    if original_language == "hi":
        english_message = translate_to_english(original_message)
        if not english_message:
            english_message = original_message
    else:
        english_message = original_message

    english_response = _build_english_response(user, english_message)

    if original_language == "hi":
        hindi_response = translate_to_hindi(english_response)
        return hindi_response or english_response

    return english_response
