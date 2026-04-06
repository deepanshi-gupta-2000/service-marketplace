from rest_framework import serializers

from bookings.serializers import BookingReadSerializer

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    booking = BookingReadSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "amount",
            "provider_earnings",
            "platform_fee",
            "method",
            "status",
            "transaction_id",
            "is_dummy",
            "created_at",
            "processed_at",
        ]
