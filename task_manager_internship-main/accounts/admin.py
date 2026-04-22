from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class AppUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role", "department")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role", "department", "email")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "department", "is_staff", "is_superuser")
    list_filter = ("role", "department", "is_staff", "is_superuser", "is_active")

