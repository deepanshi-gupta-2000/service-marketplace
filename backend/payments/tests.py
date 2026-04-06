from datetime import date, time

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from services.models import Service, ServiceProvider

from .models import Payment


class PaymentViewTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpass123",
        )
        self.provider_user = User.objects.create_user(
            username="provider",
            email="provider@example.com",
            password="testpass123",
            role="professional",
        )
        self.service = Service.objects.create(name="AC Repair", description="")
        self.provider_service = ServiceProvider.objects.create(
            user=self.provider_user,
            service=self.service,
            price=1200,
            experience=4,
            location="Delhi",
        )
        self.booking = Booking.objects.create(
            user=self.customer,
            service=self.service,
            service_provider=self.provider_service,
            location="Delhi",
            date=date(2026, 4, 10),
            time=time(11, 0),
            status=Booking.STATUS_COMPLETED,
        )

    def test_dummy_payment_is_created_for_completed_booking(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            "/api/payments/",
            {"booking": self.booking.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment = Payment.objects.get(booking=self.booking)
        self.booking.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_CREDITED)
        self.assertEqual(str(payment.provider_earnings), "1080.00")
        self.assertEqual(self.booking.payment_status, Booking.PAYMENT_CREDITED)
