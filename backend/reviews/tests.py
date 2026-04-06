from datetime import date, time

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from services.models import Service, ServiceProvider

from .models import Review


class ReviewViewTests(APITestCase):
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
        self.service = Service.objects.create(name="Cleaning", description="")
        self.provider_service = ServiceProvider.objects.create(
            user=self.provider_user,
            service=self.service,
            price=800,
            experience=2,
            location="Delhi",
        )
        self.booking = Booking.objects.create(
            user=self.customer,
            service=self.service,
            service_provider=self.provider_service,
            location="Delhi",
            date=date(2026, 4, 11),
            time=time(12, 0),
            status=Booking.STATUS_COMPLETED,
        )

    def test_completed_booking_can_be_reviewed_once(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            "/api/reviews/",
            {"booking": self.booking.id, "rating": 5, "comment": "Great job"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = Review.objects.get(booking=self.booking)
        self.assertEqual(review.provider_id, self.provider_service.id)
        self.assertEqual(review.rating, 5)
