from django.db import models
from django.utils import timezone

from bookings.models import Booking


class Payment(models.Model):
    METHOD_DUMMY = "dummy"
    METHOD_UPI = "upi"
    METHOD_CARD = "card"
    METHOD_CASH = "cash"

    METHOD_CHOICES = (
        (METHOD_DUMMY, "Dummy"),
        (METHOD_UPI, "UPI"),
        (METHOD_CARD, "Card"),
        (METHOD_CASH, "Cash"),
    )

    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CREDITED = "credited"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_CREDITED, "Credited"),
        (STATUS_FAILED, "Failed"),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    provider_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default=METHOD_DUMMY)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_dummy = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.transaction_id
