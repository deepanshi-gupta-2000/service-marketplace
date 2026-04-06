from django.conf import settings
from django.db import models
from django.utils import timezone


User = settings.AUTH_USER_MODEL


class Booking(models.Model):
    STATUS_REQUESTED = "requested"
    STATUS_ASSIGNED = "assigned"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_REQUESTED, "Requested"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_CREDITED = "credited"
    PAYMENT_FAILED = "failed"

    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_CREDITED, "Credited"),
        (PAYMENT_FAILED, "Failed"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customer_bookings",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True,
    )
    service_provider = models.ForeignKey(
        "services.ServiceProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="provider_bookings",
    )
    location = models.CharField(max_length=120, default="")
    date = models.DateField()
    time = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_REQUESTED,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING,
    )
    requested_at = models.DateTimeField(default=timezone.now)
    assigned_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.service}"


class ServiceRequest(models.Model):
    STATUS_PENDING_PROVIDER = "pending_provider_response"
    STATUS_PENDING = STATUS_PENDING_PROVIDER
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_INSPECTION_SCHEDULED = "inspection_scheduled"
    STATUS_BOOKING_CREATED = "booking_created"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_PENDING_PROVIDER, "Pending Provider Response"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_INSPECTION_SCHEDULED, "Inspection Scheduled"),
        (STATUS_BOOKING_CREATED, "Booking Created"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="service_requests",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        related_name="service_requests",
    )
    preferred_provider = models.ForeignKey(
        "services.ServiceProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_service_requests",
    )
    created_booking = models.OneToOneField(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_request",
    )
    location = models.CharField(max_length=120)
    date = models.DateField()
    time = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_PROVIDER,
    )
    provider_response_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer} - {self.service} - {self.status}"
