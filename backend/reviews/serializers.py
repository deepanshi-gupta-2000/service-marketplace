from rest_framework import serializers

from bookings.models import Booking
from bookings.serializers import BookingReadSerializer
from services.models import ServiceProvider
from services.serializers import ServiceProviderReadSerializer, UserSerializer

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    booking = BookingReadSerializer(read_only=True)
    customer = UserSerializer(read_only=True)
    provider = ServiceProviderReadSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "booking", "customer", "provider", "rating", "comment", "created_at"]


class ReviewCreateSerializer(serializers.Serializer):
    booking = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate_booking(self, value):
        try:
            booking = Booking.objects.select_related("service_provider").get(id=value)
        except Booking.DoesNotExist as error:
            raise serializers.ValidationError("Booking not found.") from error

        if booking.status != Booking.STATUS_COMPLETED:
            raise serializers.ValidationError("Only completed bookings can be reviewed.")

        if not booking.service_provider:
            raise serializers.ValidationError("Booking has no assigned provider.")

        return booking

    def create(self, validated_data):
        booking = validated_data["booking"]
        return Review.objects.create(
            booking=booking,
            customer=self.context["request"].user,
            provider=booking.service_provider,
            rating=validated_data["rating"],
            comment=validated_data.get("comment", ""),
        )
