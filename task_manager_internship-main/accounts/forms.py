from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()


class EmployeeCreateForm(forms.ModelForm):
    username = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role", "department"]

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("username") and cleaned.get("email"):
            cleaned["username"] = cleaned["email"].split("@", 1)[0]
        return cleaned


class EmployeeUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role", "department"]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["avatar", "banner"]

    def _validate_image_upload(self, field_name: str, max_mb: int = 5):
        uploaded = self.cleaned_data.get(field_name)
        if not uploaded:
            return uploaded
        content_type = getattr(uploaded, "content_type", "")
        if not content_type.startswith("image/"):
            raise forms.ValidationError("Please upload an image file.")
        if uploaded.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(f"Image must be smaller than {max_mb} MB.")
        return uploaded

    def clean_avatar(self):
        return self._validate_image_upload("avatar")

    def clean_banner(self):
        return self._validate_image_upload("banner", max_mb=10)
