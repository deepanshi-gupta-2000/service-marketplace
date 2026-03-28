# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('professional', 'Professional'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
