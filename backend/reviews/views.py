from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review
from .serializers import ReviewCreateSerializer, ReviewSerializer


class ReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        provider_id = request.query_params.get("provider")
        booking_id = request.query_params.get("booking")

        reviews = Review.objects.select_related(
            "booking",
            "customer",
            "provider",
            "provider__user",
            "provider__service",
        ).order_by("-created_at")

        if provider_id:
            reviews = reviews.filter(provider_id=provider_id)
        if booking_id:
            reviews = reviews.filter(booking_id=booking_id)

        return Response(ReviewSerializer(reviews, many=True).data)

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        booking = serializer.validated_data["booking"]
        if booking.user_id != request.user.id:
            return Response(
                {"error": "You can only review your own bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if hasattr(booking, "review"):
            return Response(
                {"error": "A review already exists for this booking."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
