from __future__ import annotations


HIGH_PRIORITY_WORDS = ("urgent", "asap", "immediately")
LOW_PRIORITY_WORDS = ("later", "optional")


def suggest_task_priority(title: str, description: str) -> str:
    """
    Return a simple priority suggestion from task text.
    """
    content = f"{title} {description}".lower()

    if any(word in content for word in HIGH_PRIORITY_WORDS):
        return "HIGH"
    if any(word in content for word in LOW_PRIORITY_WORDS):
        return "LOW"
    return "MEDIUM"
