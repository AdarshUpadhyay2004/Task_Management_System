from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import NoteForm
from .models import Note


def _get_user_note(user, note_id: int) -> Note:
    return get_object_or_404(Note, pk=note_id, user=user)


@login_required
@require_GET
def note_list(request):
    search_query = (request.GET.get("q") or "").strip()
    notes = Note.objects.filter(user=request.user)

    if search_query:
        notes = notes.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))

    context = {
        "notes": notes,
        "create_form": NoteForm(),
        "search_query": search_query,
        "editing_note_id": request.GET.get("edit"),
    }
    return render(request, "notes/note_list.html", context)


@login_required
@require_POST
def note_create(request):
    form = NoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.user = request.user
        note.save()
        messages.success(request, "Note created successfully.")
    else:
        messages.error(request, "Please correct the errors in the note form.")
    return redirect("note_list")


@login_required
@require_POST
def note_update(request, note_id: int):
    note = _get_user_note(request.user, note_id)
    form = NoteForm(request.POST, instance=note)
    if form.is_valid():
        form.save()
        messages.success(request, "Note updated successfully.")
    else:
        messages.error(request, "Could not update the note. Please check the form fields.")
    return redirect("note_list")


@login_required
@require_POST
def note_delete(request, note_id: int):
    note = _get_user_note(request.user, note_id)
    note.delete()
    messages.success(request, "Note deleted successfully.")
    return redirect("note_list")


@login_required
@require_POST
def note_toggle_pin(request, note_id: int):
    note = _get_user_note(request.user, note_id)
    note.is_pinned = not note.is_pinned
    note.save(update_fields=["is_pinned", "updated_at"])
    messages.success(request, "Note updated successfully.")
    return redirect("note_list")
