import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .logic import analyze_message
from .models import ChatMessage
from .utils import detect_language


@login_required
@require_http_methods(["GET", "POST"])
def chat_view(request):
    if request.method == "GET":
        messages = ChatMessage.objects.filter(user=request.user).order_by("-timestamp")[:20]
        return render(
            request,
            "chatbot/chat.html",
            {"chat_messages": reversed(messages)},
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    user_message = (payload.get("message") or "").strip()
    if not user_message:
        return JsonResponse({"error": "Message is required."}, status=400)

    detected_language = detect_language(user_message)
    bot_response = analyze_message(request.user, user_message)
    ChatMessage.objects.create(
        user=request.user,
        message=user_message,
        response=bot_response,
    )
    return JsonResponse(
        {
            "message": user_message,
            "response": bot_response,
            "language": detected_language,
        }
    )
