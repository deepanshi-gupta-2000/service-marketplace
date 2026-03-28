from django.db import models

# Create your models here.
from django.db import models
from bookings.models import Booking

class Payment(models.Model):
    METHOD_CHOICES = (
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('cash', 'Cash'),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=100)

    def __str__(self):
        return self.transaction_id