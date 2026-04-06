from django.db.models import Avg, Count, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from services.models import Service, ServiceProvider

from .models import Booking, ServiceRequest
from .serializers import (
    BookingReadSerializer,
    BookingStatusSerializer,
    ServiceRequestActionSerializer,
    ServiceRequestCreateSerializer,
    ServiceRequestReadSerializer,
)


class BookingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _candidate_providers(service_id, location, booking_time):
        active_statuses = [
            Booking.STATUS_REQUESTED,
            Booking.STATUS_ASSIGNED,
            Booking.STATUS_IN_PROGRESS,
        ]
        candidates = (
            ServiceProvider.objects.select_related("user", "service", "user__provider_profile")
            .filter(service_id=service_id)
            .annotate(
                average_rating=Coalesce(Avg("reviews__rating"), Value(0.0)),
                active_jobs=Count(
                    "provider_bookings",
                    filter=Q(provider_bookings__status__in=active_statuses),
                    distinct=True,
                ),
            )
        )

        if location:
            candidates = candidates.filter(location__icontains=location)

        candidates = candidates.filter(
            Q(user__provider_profile__isnull=True)
            | Q(user__provider_profile__is_accepting_jobs=True)
        )

        if booking_time:
            candidates = candidates.filter(
                Q(user__provider_profile__available_from__isnull=True)
                | Q(user__provider_profile__available_to__isnull=True)
                | (
                    Q(user__provider_profile__available_from__lte=booking_time)
                    & Q(user__provider_profile__available_to__gte=booking_time)
                )
            )

        return candidates.order_by("-average_rating", "active_jobs", "price", "-experience")

    def get(self, request):
        user_id = request.query_params.get("user")
        provider_id = request.query_params.get("provider")
        status_value = request.query_params.get("status")

        bookings = Booking.objects.select_related(
            "user",
            "service",
            "service_provider",
            "service_provider__user",
            "service_provider__service",
        ).all()

        if user_id:
            bookings = bookings.filter(user_id=user_id)
        if provider_id:
            bookings = bookings.filter(service_provider_id=provider_id)
        if status_value:
            bookings = bookings.filter(status=status_value)

        serializer = BookingReadSerializer(bookings.order_by("-requested_at"), many=True)
        return Response(serializer.data)

    def post(self, request):
        return Response(
            {"error": "Customers must send a service request first. Use /api/bookings/requests/."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request):
        serializer = BookingStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        booking_id = serializer.validated_data["id"]
        new_status = serializer.validated_data["status"]

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        allowed_transitions = {
            Booking.STATUS_REQUESTED: {Booking.STATUS_ASSIGNED, Booking.STATUS_CANCELLED},
            Booking.STATUS_ASSIGNED: {Booking.STATUS_IN_PROGRESS, Booking.STATUS_CANCELLED},
            Booking.STATUS_IN_PROGRESS: {Booking.STATUS_COMPLETED, Booking.STATUS_CANCELLED},
            Booking.STATUS_COMPLETED: set(),
            Booking.STATUS_CANCELLED: set(),
        }

        if new_status not in allowed_transitions.get(booking.status, set()):
            return Response(
                {"error": f"Cannot transition booking from {booking.status} to {new_status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = new_status
        if new_status == Booking.STATUS_ASSIGNED and booking.assigned_at is None:
            booking.assigned_at = timezone.now()
        if new_status == Booking.STATUS_COMPLETED:
            booking.completed_at = timezone.now()
        booking.save()

        return Response(BookingReadSerializer(booking).data)


class ServiceRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _candidate_providers(service_id, location, booking_time):
        active_statuses = [
            Booking.STATUS_REQUESTED,
            Booking.STATUS_ASSIGNED,
            Booking.STATUS_IN_PROGRESS,
        ]
        candidates = (
            ServiceProvider.objects.select_related("user", "service", "user__provider_profile")
            .filter(service_id=service_id, is_active=True)
            .annotate(
                average_rating=Coalesce(Avg("reviews__rating"), Value(0.0)),
                active_jobs=Count(
                    "provider_bookings",
                    filter=Q(provider_bookings__status__in=active_statuses),
                    distinct=True,
                ),
            )
        )

        if location:
            candidates = candidates.filter(location__icontains=location)

        candidates = candidates.filter(
            Q(user__provider_profile__isnull=True)
            | (
                Q(user__provider_profile__is_accepting_jobs=True)
                & Q(user__provider_profile__is_active_provider=True)
            )
        )

        if booking_time:
            candidates = candidates.filter(
                Q(user__provider_profile__available_from__isnull=True)
                | Q(user__provider_profile__available_to__isnull=True)
                | (
                    Q(user__provider_profile__available_from__lte=booking_time)
                    & Q(user__provider_profile__available_to__gte=booking_time)
                )
            )

        return candidates.order_by("-average_rating", "active_jobs", "price", "-experience")

    def get(self, request):
        customer_id = request.query_params.get("customer")
        provider_user_id = request.query_params.get("provider_user")
        status_value = request.query_params.get("status")

        requests = ServiceRequest.objects.select_related(
            "customer",
            "service",
            "preferred_provider",
            "preferred_provider__user",
            "preferred_provider__service",
            "created_booking",
            "created_booking__service",
            "created_booking__service_provider",
            "created_booking__service_provider__user",
            "created_booking__service_provider__service",
        ).all()

        if customer_id:
            requests = requests.filter(customer_id=customer_id)
        if provider_user_id:
            requests = requests.filter(preferred_provider__user_id=provider_user_id)
        if status_value:
            requests = requests.filter(status=status_value)

        serializer = ServiceRequestReadSerializer(requests.order_by("-created_at"), many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ServiceRequestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        service = validated_data["service"]
        provider = validated_data.get("preferred_provider")

        if provider and provider.service_id != service.id:
            return Response(
                {"error": "Selected provider does not offer the requested service."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if provider and not provider.is_active:
            return Response(
                {"error": "Selected provider is not currently active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not provider:
            provider = self._candidate_providers(
                service.id,
                validated_data.get("location"),
                validated_data.get("time"),
            ).first()

        if not provider:
            return Response(
                {"error": "No active provider matches this service and location right now."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request = ServiceRequest.objects.create(
            customer=request.user,
            service=service,
            preferred_provider=provider,
            location=validated_data["location"],
            date=validated_data["date"],
            time=validated_data["time"],
            notes=validated_data.get("notes", ""),
        )

        read_serializer = ServiceRequestReadSerializer(service_request)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        serializer = ServiceRequestActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        request_id = serializer.validated_data["id"]
        action = serializer.validated_data["action"]
        response_notes = serializer.validated_data.get("provider_response_notes", "")

        try:
            service_request = ServiceRequest.objects.select_related(
                "customer",
                "service",
                "preferred_provider",
                "preferred_provider__user",
            ).get(id=request_id)
        except ServiceRequest.DoesNotExist:
            return Response({"error": "Service request not found."}, status=status.HTTP_404_NOT_FOUND)

        if action == "cancel":
            if service_request.customer_id != request.user.id:
                return Response(
                    {"error": "Only the customer can cancel this request."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if service_request.status != ServiceRequest.STATUS_PENDING:
                return Response(
                    {"error": "Only pending requests can be cancelled."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            service_request.status = ServiceRequest.STATUS_CANCELLED
            service_request.responded_at = timezone.now()
            service_request.save(update_fields=["status", "responded_at"])
            return Response(ServiceRequestReadSerializer(service_request).data)

        provider = service_request.preferred_provider
        if not provider or provider.user_id != request.user.id:
            return Response(
                {"error": "Only the selected provider can respond to this request."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if service_request.status != ServiceRequest.STATUS_PENDING:
            return Response(
                {"error": "Only pending requests can be updated by the provider."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request.provider_response_notes = response_notes
        service_request.responded_at = timezone.now()

        if action == "reject":
            service_request.status = ServiceRequest.STATUS_REJECTED
            service_request.save(update_fields=["status", "provider_response_notes", "responded_at"])
            return Response(ServiceRequestReadSerializer(service_request).data)

        service = service_request.service
        provider_pricing_type = provider.pricing_type or service.pricing_type
        if provider_pricing_type in [Service.PRICING_INSPECTION, Service.PRICING_CUSTOM_QUOTE]:
            service_request.status = ServiceRequest.STATUS_INSPECTION_SCHEDULED
            service_request.save(update_fields=["status", "provider_response_notes", "responded_at"])
            return Response(ServiceRequestReadSerializer(service_request).data)

        booking = Booking.objects.create(
            user=service_request.customer,
            service=service,
            service_provider=provider,
            location=service_request.location,
            date=service_request.date,
            time=service_request.time,
            notes=service_request.notes,
            status=Booking.STATUS_ASSIGNED,
            assigned_at=timezone.now(),
        )
        service_request.status = ServiceRequest.STATUS_BOOKING_CREATED
        service_request.created_booking = booking
        service_request.save(
            update_fields=[
                "status",
                "provider_response_notes",
                "responded_at",
                "created_booking",
            ]
        )

        return Response(ServiceRequestReadSerializer(service_request).data)
