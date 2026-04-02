from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_bookings'   # 🔥 important
    )

    service_provider = models.ForeignKey(
        'services.ServiceProvider',
        on_delete=models.CASCADE,
        related_name='provider_bookings'   # 🔥 important
    )

    date = models.DateField()
    time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    payment_status = models.CharField(
        max_length=20,
        default='pending'
    )

    def __str__(self):
        return f"{self.user} - {self.service_provider}"