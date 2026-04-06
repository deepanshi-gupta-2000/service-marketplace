from django.db import models
from django.conf import settings
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower


class Service(models.Model):
    PRICING_FIXED = "fixed"
    PRICING_STARTING_FROM = "starting_from"
    PRICING_INSPECTION = "inspection"
    PRICING_CUSTOM_QUOTE = "custom_quote"

    PRICING_CHOICES = (
        (PRICING_FIXED, "Fixed Price"),
        (PRICING_STARTING_FROM, "Starting From"),
        (PRICING_INSPECTION, "Inspection Required"),
        (PRICING_CUSTOM_QUOTE, "Custom Quote"),
    )

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        constraints = [
            UniqueConstraint(Lower("name"), name="unique_service_name")
        ]

    description = models.TextField(blank=True, default="")
    pricing_type = models.CharField(
        max_length=20,
        choices=PRICING_CHOICES,
        default=PRICING_FIXED,
    )
    starting_price = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProviderProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )
    display_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    skills_summary = models.TextField(blank=True)
    availability_notes = models.TextField(blank=True)
    default_location = models.CharField(max_length=120, blank=True)
    available_from = models.TimeField(null=True, blank=True)
    available_to = models.TimeField(null=True, blank=True)
    is_accepting_jobs = models.BooleanField(default=True)
    is_active_provider = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.user.username


class ServiceProvider(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    price = models.IntegerField()
    pricing_type = models.CharField(
        max_length=20,
        choices=Service.PRICING_CHOICES,
        default=Service.PRICING_FIXED,
    )
    experience = models.IntegerField(default=0)
    location = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "service"], name="unique_provider_service"),
        ]

    def __str__(self):
        return f"{self.user} - {self.service}"

