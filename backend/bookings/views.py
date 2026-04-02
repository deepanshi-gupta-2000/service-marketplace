from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Booking
from .serializers import BookingSerializer

class BookingView(APIView):

    # ✅ Create booking
    def post(self, request):
        serializer = BookingSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Get all bookings
    # def get(self, request):
    #     bookings = Booking.objects.all()
    #     serializer = BookingSerializer(bookings, many=True)
    #     return Response(serializer.data)
    
    def get(self, request):
        user_id = request.query_params.get('user')
        provider_id = request.query_params.get('provider')

        bookings = Booking.objects.all()

        if user_id:
            bookings = bookings.filter(user_id=user_id)

        if provider_id:
            bookings = bookings.filter(service_provider_id=provider_id)

        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
    def patch(self, request):
        booking_id = request.data.get('id')

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        booking.status = request.data.get('status')
        booking.save()

        return Response({"message": "Status updated"})
