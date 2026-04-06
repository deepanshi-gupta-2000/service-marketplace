from rest_framework import serializers

from services.serializers import ServiceProviderReadSerializer, ServiceSerializer, UserSerializer

from .models import Booking, ServiceRequest


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id",
            "service",
            "service_provider",
            "location",
            "date",
            "time",
            "notes",
            "status",
            "payment_status",
        ]
        read_only_fields = ["id", "status", "payment_status"]


class BookingReadSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    service = ServiceSerializer(allow_null=True)
    service_provider = ServiceProviderReadSerializer(allow_null=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "service",
            "service_provider",
            "location",
            "date",
            "time",
            "notes",
            "status",
            "payment_status",
            "requested_at",
            "assigned_at",
            "completed_at",
        ]


class BookingStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Booking.STATUS_CHOICES)


class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "service",
            "preferred_provider",
            "location",
            "date",
            "time",
            "notes",
        ]
        read_only_fields = ["id"]


class ServiceRequestReadSerializer(serializers.ModelSerializer):
    customer = UserSerializer()
    service = ServiceSerializer()
    preferred_provider = ServiceProviderReadSerializer(allow_null=True)
    created_booking = BookingReadSerializer(allow_null=True)

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "customer",
            "service",
            "preferred_provider",
            "created_booking",
            "location",
            "date",
            "time",
            "notes",
            "status",
            "provider_response_notes",
            "created_at",
            "responded_at",
        ]


class ServiceRequestActionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=["accept", "reject", "cancel"])
    provider_response_notes = serializers.CharField(required=False, allow_blank=True)
