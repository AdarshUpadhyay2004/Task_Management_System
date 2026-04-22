from django import forms
from django.contrib.auth import get_user_model

from .models import Task


User = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assigned_to", "status", "due_date", "estimated_hours"]

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)
        queryset = User.objects.filter(role=User.Role.EMPLOYEE).order_by("first_name", "last_name", "email")
        if current_user and getattr(current_user, "role", None) == User.Role.TEAM_LEAD and current_user.department:
            queryset = queryset.filter(department=current_user.department)
        self.fields["assigned_to"].queryset = queryset
        self.fields["due_date"].widget = forms.DateInput(attrs={"type": "date"})
        self.fields["estimated_hours"].widget = forms.NumberInput(attrs={"step": "0.5", "min": "0"})
