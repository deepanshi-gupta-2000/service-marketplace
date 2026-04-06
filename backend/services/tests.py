from datetime import time

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from payments.models import Payment
from reviews.models import Review

from .models import ProviderProfile, Service, ServiceProvider


class ServiceProviderViewTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="deepa",
            email="deepa@example.com",
            password="testpass123",
        )
        self.url = "/api/providers/"

    def test_provider_profile_can_be_created_for_current_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/providers/profile/",
            {
                "display_name": "Deepa Services",
                "bio": "Trusted home services",
                "skills_summary": "Cleaning, Plumbing",
                "default_location": "Delhi",
                "available_from": "09:00:00",
                "available_to": "18:00:00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = ProviderProfile.objects.get(user=self.user)
        self.assertEqual(profile.display_name, "Deepa Services")
        self.assertEqual(profile.available_from, time(9, 0))

    def test_register_provider_creates_multiple_services_and_upgrades_role(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                "service_names": ["Painting", "Cleaning"],
                "price": 500,
                "pricing_type": Service.PRICING_STARTING_FROM,
                "location": "Delhi",
                "experience": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "professional")
        self.assertEqual(ServiceProvider.objects.filter(user=self.user).count(), 2)
        self.assertEqual(len(response.data["providers"]), 2)
        self.assertEqual(response.data["providers"][0]["pricing_type"], Service.PRICING_STARTING_FROM)

    def test_register_provider_skips_existing_service_and_creates_new_one(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            self.url,
            {
                "service_name": "Painting",
                "price": 500,
                "location": "Delhi",
            },
            format="json",
        )

        response = self.client.post(
            self.url,
            {
                "service_names": ["Painting", "Plumbing"],
                "price": 700,
                "location": "Delhi",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceProvider.objects.filter(user=self.user).count(), 2)
        self.assertEqual(response.data["skipped_services"], ["Painting"])

    def test_stepping_down_preserves_provider_history_but_deactivates_profile(self):
        self.client.force_authenticate(user=self.user)
        profile = ProviderProfile.objects.create(user=self.user, display_name="Deepa Services")
        service = Service.objects.create(name="Cleaning", description="")
        provider = ServiceProvider.objects.create(
            user=self.user,
            service=service,
            price=500,
            experience=2,
            location="Delhi",
            is_active=True,
        )
        self.user.role = "professional"
        self.user.save(update_fields=["role"])
        booking = Booking.objects.create(
            user=self.user,
            service=service,
            service_provider=provider,
            location="Delhi",
            date="2026-04-15",
            time="10:00:00",
            status=Booking.STATUS_COMPLETED,
        )
        Review.objects.create(
            booking=booking,
            customer=self.user,
            provider=provider,
            rating=5,
            comment="Great",
        )

        response = self.client.delete("/api/providers/profile/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        profile.refresh_from_db()
        provider.refresh_from_db()
        self.assertEqual(self.user.role, "customer")
        self.assertFalse(profile.is_active_provider)
        self.assertFalse(profile.is_accepting_jobs)
        self.assertFalse(provider.is_active)
        self.assertEqual(ServiceProvider.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Review.objects.filter(provider=provider).count(), 1)

    def test_rejoining_reactivates_existing_service_record(self):
        self.client.force_authenticate(user=self.user)
        profile = ProviderProfile.objects.create(
            user=self.user,
            display_name="Deepa Services",
            is_active_provider=False,
            is_accepting_jobs=False,
        )
        service = Service.objects.create(name="Cleaning", description="")
        provider = ServiceProvider.objects.create(
            user=self.user,
            service=service,
            price=500,
            experience=2,
            location="Delhi",
            is_active=False,
        )

        response = self.client.post(
            self.url,
            {
                "service_names": ["Cleaning"],
                "price": 900,
                "location": "Mumbai",
                "experience": 6,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        profile.refresh_from_db()
        provider.refresh_from_db()
        self.assertEqual(self.user.role, "professional")
        self.assertTrue(profile.is_active_provider)
        self.assertTrue(profile.is_accepting_jobs)
        self.assertTrue(provider.is_active)
        self.assertEqual(provider.price, 900)
        self.assertEqual(provider.location, "Mumbai")

    def test_professional_can_update_existing_service_details(self):
        self.client.force_authenticate(user=self.user)
        service = Service.objects.create(name="Painting", description="")
        provider = ServiceProvider.objects.create(
            user=self.user,
            service=service,
            price=500,
            experience=2,
            location="Delhi",
            is_active=True,
        )

        response = self.client.patch(
            f"/api/providers/{provider.id}/",
            {
                "price": 850,
                "pricing_type": Service.PRICING_INSPECTION,
                "experience": 5,
                "location": "Mumbai",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        provider.refresh_from_db()
        self.assertEqual(provider.price, 850)
        self.assertEqual(provider.pricing_type, Service.PRICING_INSPECTION)
        self.assertEqual(provider.experience, 5)
        self.assertEqual(provider.location, "Mumbai")

    def test_provider_list_exposes_provider_specific_pricing_metadata(self):
        self.client.force_authenticate(user=self.user)
        service = Service.objects.create(
            name="AC Repair",
            description="Fix AC issues",
            pricing_type=Service.PRICING_FIXED,
            starting_price=499,
        )
        ServiceProvider.objects.create(
            user=self.user,
            service=service,
            price=799,
            pricing_type=Service.PRICING_STARTING_FROM,
            experience=2,
            location="Delhi",
            is_active=True,
        )

        response = self.client.get(f"/api/providers/?service={service.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["pricing_type"], Service.PRICING_STARTING_FROM)
        self.assertEqual(response.data[0]["pricing_display"], "Starts at Rs. 799")

    def test_provider_list_supports_location_price_rating_filters_and_sort(self):
        customer = get_user_model().objects.create_user(
            username="customer1",
            email="customer1@example.com",
            password="testpass123",
        )
        provider_user_1 = get_user_model().objects.create_user(
            username="pro1",
            email="pro1@example.com",
            password="testpass123",
            role="professional",
        )
        provider_user_2 = get_user_model().objects.create_user(
            username="pro2",
            email="pro2@example.com",
            password="testpass123",
            role="professional",
        )
        ProviderProfile.objects.create(user=provider_user_1, is_active_provider=True, is_accepting_jobs=True)
        ProviderProfile.objects.create(user=provider_user_2, is_active_provider=True, is_accepting_jobs=True)
        service = Service.objects.create(name="Refurbishment", description="", pricing_type="inspection")
        provider_one = ServiceProvider.objects.create(
            user=provider_user_1,
            service=service,
            price=15000,
            experience=8,
            location="Agra",
            is_active=True,
        )
        provider_two = ServiceProvider.objects.create(
            user=provider_user_2,
            service=service,
            price=9000,
            experience=3,
            location="Agra",
            is_active=True,
        )
        booking_one = Booking.objects.create(
            user=customer,
            service=service,
            service_provider=provider_one,
            location="Agra",
            date="2026-04-20",
            time="10:00:00",
            status=Booking.STATUS_COMPLETED,
        )
        booking_two = Booking.objects.create(
            user=customer,
            service=service,
            service_provider=provider_two,
            location="Agra",
            date="2026-04-21",
            time="11:00:00",
            status=Booking.STATUS_COMPLETED,
        )
        Review.objects.create(booking=booking_one, customer=customer, provider=provider_one, rating=5)
        Review.objects.create(booking=booking_two, customer=customer, provider=provider_two, rating=3)

        response = self.client.get(
            f"/api/providers/?service={service.id}&location=Agra&max_price=12000&min_rating=2&sort_by=lowest_price"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"]["username"], "pro2")

    def test_service_serializer_exposes_pricing_metadata(self):
        service = Service.objects.create(
            name="AC Repair",
            description="Fix AC issues",
            pricing_type=Service.PRICING_STARTING_FROM,
            starting_price=499,
        )

        response = self.client.get("/api/services/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        matching = next(item for item in response.data if item["id"] == service.id)
        self.assertEqual(matching["pricing_type"], Service.PRICING_STARTING_FROM)
        self.assertEqual(matching["starting_price"], 499)

    def test_provider_dashboard_returns_summary_profile_reviews_and_payments(self):
        self.client.force_authenticate(user=self.user)
        self.user.role = "professional"
        self.user.save(update_fields=["role"])
        profile = ProviderProfile.objects.create(
            user=self.user,
            display_name="Deepa Services",
            default_location="Delhi",
            is_active_provider=True,
            is_accepting_jobs=True,
        )
        service = Service.objects.create(name="Cleaning", description="")
        provider = ServiceProvider.objects.create(
            user=self.user,
            service=service,
            price=800,
            experience=4,
            location="Delhi",
            is_active=True,
        )
        customer = get_user_model().objects.create_user(
            username="customer2",
            email="customer2@example.com",
            password="testpass123",
        )
        booking = Booking.objects.create(
            user=customer,
            service=service,
            service_provider=provider,
            location="Delhi",
            date="2026-04-22",
            time="10:00:00",
            status=Booking.STATUS_COMPLETED,
            payment_status=Booking.PAYMENT_CREDITED,
        )
        Review.objects.create(
            booking=booking,
            customer=customer,
            provider=provider,
            rating=5,
            comment="Great work",
        )
        Payment.objects.create(
            booking=booking,
            amount="800.00",
            provider_earnings="720.00",
            platform_fee="80.00",
            method=Payment.METHOD_DUMMY,
            status=Payment.STATUS_CREDITED,
            transaction_id="dummy-payment-1",
            is_dummy=True,
        )

        response = self.client.get("/api/providers/dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profile"]["display_name"], profile.display_name)
        self.assertEqual(response.data["summary"]["active_service_count"], 1)
        self.assertEqual(response.data["summary"]["review_count"], 1)
        self.assertEqual(response.data["summary"]["average_rating"], 5.0)
        self.assertEqual(response.data["summary"]["total_earnings"], 720.0)
        self.assertEqual(len(response.data["recent_reviews"]), 1)
        self.assertEqual(len(response.data["recent_payments"]), 1)
