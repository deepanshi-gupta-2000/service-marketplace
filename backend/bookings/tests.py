from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from services.models import ProviderProfile, Service, ServiceProvider

from .models import Booking, ServiceRequest


class ServiceRequestFlowTests(APITestCase):
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
        ProviderProfile.objects.create(
            user=self.provider_user,
            display_name="Provider One",
            default_location="Delhi",
            is_accepting_jobs=True,
            is_active_provider=True,
        )
        self.fixed_service = Service.objects.create(
            name="Plumbing",
            description="",
            pricing_type=Service.PRICING_FIXED,
            starting_price=500,
        )
        self.inspection_service = Service.objects.create(
            name="Refurbishment",
            description="",
            pricing_type=Service.PRICING_INSPECTION,
        )
        self.fixed_provider = ServiceProvider.objects.create(
            user=self.provider_user,
            service=self.fixed_service,
            price=500,
            pricing_type=Service.PRICING_FIXED,
            experience=5,
            location="Delhi",
            is_active=True,
        )
        self.inspection_provider = ServiceProvider.objects.create(
            user=self.provider_user,
            service=self.inspection_service,
            price=1500,
            pricing_type=Service.PRICING_INSPECTION,
            experience=8,
            location="Delhi",
            is_active=True,
        )

    def test_customer_creates_service_request_for_selected_provider(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            "/api/bookings/requests/",
            {
                "service": self.fixed_service.id,
                "preferred_provider": self.fixed_provider.id,
                "location": "Delhi",
                "date": "2026-04-10",
                "time": "10:00:00",
                "notes": "Kitchen sink issue",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        request_obj = ServiceRequest.objects.get(id=response.data["id"])
        self.assertEqual(request_obj.status, ServiceRequest.STATUS_PENDING)
        self.assertEqual(request_obj.preferred_provider_id, self.fixed_provider.id)

    def test_provider_accepting_fixed_service_request_creates_booking(self):
        request_obj = ServiceRequest.objects.create(
            customer=self.customer,
            service=self.fixed_service,
            preferred_provider=self.fixed_provider,
            location="Delhi",
            date="2026-04-10",
            time="10:00:00",
            notes="Kitchen sink issue",
        )

        self.client.force_authenticate(user=self.provider_user)
        response = self.client.patch(
            "/api/bookings/requests/",
            {"id": request_obj.id, "action": "accept", "provider_response_notes": "Confirmed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, ServiceRequest.STATUS_BOOKING_CREATED)
        self.assertIsNotNone(request_obj.created_booking)
        self.assertEqual(request_obj.created_booking.status, Booking.STATUS_ASSIGNED)

    def test_provider_accepting_inspection_service_request_schedules_inspection(self):
        request_obj = ServiceRequest.objects.create(
            customer=self.customer,
            service=self.inspection_service,
            preferred_provider=self.inspection_provider,
            location="Delhi",
            date="2026-04-10",
            time="10:00:00",
            notes="Need full home estimate",
        )

        self.client.force_authenticate(user=self.provider_user)
        response = self.client.patch(
            "/api/bookings/requests/",
            {"id": request_obj.id, "action": "accept"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, ServiceRequest.STATUS_INSPECTION_SCHEDULED)
        self.assertIsNone(request_obj.created_booking)

    def test_provider_specific_pricing_type_controls_acceptance_flow(self):
        direct_service = Service.objects.create(
            name="Painter",
            description="",
            pricing_type=Service.PRICING_FIXED,
            starting_price=1000,
        )
        inspection_provider = ServiceProvider.objects.create(
            user=self.provider_user,
            service=direct_service,
            price=1800,
            pricing_type=Service.PRICING_INSPECTION,
            experience=3,
            location="Delhi",
            is_active=True,
        )
        request_obj = ServiceRequest.objects.create(
            customer=self.customer,
            service=direct_service,
            preferred_provider=inspection_provider,
            location="Delhi",
            date="2026-04-11",
            time="11:00:00",
            notes="Need site visit first",
        )

        self.client.force_authenticate(user=self.provider_user)
        response = self.client.patch(
            "/api/bookings/requests/",
            {"id": request_obj.id, "action": "accept"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, ServiceRequest.STATUS_INSPECTION_SCHEDULED)

    def test_booking_status_transitions_follow_lifecycle(self):
        self.client.force_authenticate(user=self.customer)
        booking = Booking.objects.create(
            user=self.customer,
            service=self.fixed_service,
            service_provider=self.fixed_provider,
            location="Delhi",
            date="2026-04-10",
            time="10:00:00",
            status=Booking.STATUS_ASSIGNED,
        )

        progress_response = self.client.patch(
            "/api/bookings/",
            {"id": booking.id, "status": Booking.STATUS_IN_PROGRESS},
            format="json",
        )
        complete_response = self.client.patch(
            "/api/bookings/",
            {"id": booking.id, "status": Booking.STATUS_COMPLETED},
            format="json",
        )

        self.assertEqual(progress_response.status_code, status.HTTP_200_OK)
        self.assertEqual(complete_response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_COMPLETED)
        self.assertIsNotNone(booking.completed_at)
