from django import forms

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content", "is_pinned"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-sky-500 focus:outline-none",
                    "placeholder": "Enter note title",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "min-h-40 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-sky-500 focus:outline-none",
                    "placeholder": "Write your note here...",
                }
            ),
            "is_pinned": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500",
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Title is required.")
        return title

    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError("Content is required.")
        return content
