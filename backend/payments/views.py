import uuid
from decimal import Decimal

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking

from .models import Payment
from .serializers import PaymentSerializer


class PaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        booking_id = request.query_params.get("booking")
        payments = Payment.objects.select_related(
            "booking",
            "booking__user",
            "booking__service",
            "booking__service_provider",
            "booking__service_provider__user",
            "booking__service_provider__service",
        ).all()

        if booking_id:
            payments = payments.filter(booking_id=booking_id)

        return Response(PaymentSerializer(payments.order_by("-created_at"), many=True).data)

    def post(self, request):
        booking_id = request.data.get("booking")
        method = request.data.get("method", Payment.METHOD_DUMMY)

        if not booking_id:
            return Response(
                {"error": "Booking is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking = Booking.objects.select_related("service_provider").get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

        if booking.status != Booking.STATUS_COMPLETED:
            return Response(
                {"error": "Payments can only be processed after the service is completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment, created = Payment.objects.get_or_create(
            booking=booking,
            defaults={
                "amount": Decimal(str(booking.service_provider.price)),
                "platform_fee": (Decimal(str(booking.service_provider.price)) * Decimal("0.10")).quantize(
                    Decimal("0.01")
                ),
                "provider_earnings": (Decimal(str(booking.service_provider.price)) * Decimal("0.90")).quantize(
                    Decimal("0.01")
                ),
                "method": method,
                "status": Payment.STATUS_CREDITED,
                "transaction_id": f"dummy-{uuid.uuid4().hex[:12]}",
                "is_dummy": True,
                "processed_at": timezone.now(),
            },
        )

        if not created:
            return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)

        booking.payment_status = Booking.PAYMENT_CREDITED
        booking.save(update_fields=["payment_status"])

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
