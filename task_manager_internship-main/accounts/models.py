from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        TEAM_LEAD = "TEAM_LEAD", "Team Lead"
        EMPLOYEE = "EMPLOYEE", "Employee"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    department = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    avatar = models.FileField(upload_to="profiles/avatars/", blank=True, null=True)
    banner = models.FileField(upload_to="profiles/banners/", blank=True, null=True)


# Create your models here.
