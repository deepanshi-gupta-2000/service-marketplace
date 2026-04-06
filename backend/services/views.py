from django.db.models import Avg, Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking, ServiceRequest
from payments.models import Payment
from reviews.models import Review

from .models import ProviderProfile, Service, ServiceProvider
from .serializers import (
    ProviderProfileSerializer,
    ServiceProviderReadSerializer,
    ServiceProviderSerializer,
    ServiceSerializer,
)


def get_service_defaults(service_name):
    normalized = service_name.strip().lower()
    if normalized == "refurbishment":
        return {
            "description": "",
            "pricing_type": Service.PRICING_INSPECTION,
            "starting_price": None,
        }

    return {"description": ""}


class ServiceListView(APIView):
    def get(self, request):
        services = Service.objects.all().order_by("name")
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

    def post(self, request):
        payload = request.data.copy()
        service_name = str(payload.get("name", "")).strip()
        if service_name.lower() == "refurbishment" and not payload.get("pricing_type"):
            payload["pricing_type"] = Service.PRICING_INSPECTION
            payload["starting_price"] = None

        serializer = ServiceSerializer(data=payload)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProviderProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = ProviderProfile.objects.get_or_create(user=request.user)
        return Response(ProviderProfileSerializer(profile).data)

    def put(self, request):
        profile, _ = ProviderProfile.objects.get_or_create(user=request.user)
        serializer = ProviderProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        profile, _ = ProviderProfile.objects.get_or_create(user=user)
        profile.is_active_provider = False
        profile.is_accepting_jobs = False
        profile.save(update_fields=["is_active_provider", "is_accepting_jobs", "updated_at"])

        deactivated_services = list(
            ServiceProvider.objects.filter(user=user, is_active=True).values_list("service__name", flat=True)
        )
        ServiceProvider.objects.filter(user=user).update(is_active=False)

        if user.role != "customer":
            user.role = "customer"
            user.save(update_fields=["role"])

        return Response(
            {
                "message": "Professional profile deactivated. Account reverted to customer.",
                "deactivated_services": deactivated_services,
            },
            status=status.HTTP_200_OK,
        )


class ProviderDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = ProviderProfile.objects.get_or_create(user=request.user)
        provider_services = ServiceProviderView._annotated_queryset().filter(user=request.user)
        provider_ids = list(provider_services.values_list("id", flat=True))

        bookings = Booking.objects.select_related(
            "user",
            "service",
            "service_provider",
            "service_provider__user",
            "service_provider__service",
        ).filter(service_provider__user=request.user)
        reviews = Review.objects.select_related(
            "booking",
            "customer",
            "provider",
            "provider__service",
            "provider__user",
        ).filter(provider__user=request.user)
        payments = Payment.objects.select_related(
            "booking",
            "booking__service",
            "booking__user",
            "booking__service_provider",
            "booking__service_provider__user",
            "booking__service_provider__service",
        ).filter(booking__service_provider__user=request.user)
        pending_requests = ServiceRequest.objects.select_related(
            "customer",
            "service",
            "preferred_provider",
            "preferred_provider__service",
            "preferred_provider__user",
        ).filter(
            preferred_provider__user=request.user,
            status=ServiceRequest.STATUS_PENDING,
        )

        average_rating = reviews.aggregate(value=Coalesce(Avg("rating"), Value(0.0)))["value"] or 0.0
        total_earnings = payments.aggregate(value=Sum("provider_earnings"))["value"] or 0.0
        total_platform_fee = payments.aggregate(value=Sum("platform_fee"))["value"] or 0.0

        active_statuses = [Booking.STATUS_ASSIGNED, Booking.STATUS_IN_PROGRESS]
        active_bookings = bookings.filter(status__in=active_statuses).order_by("date", "time")[:5]
        recent_payments = payments.order_by("-created_at")[:5]
        recent_reviews = reviews.order_by("-created_at")[:5]

        return Response(
            {
                "profile": ProviderProfileSerializer(profile).data,
                "summary": {
                    "active_service_count": provider_services.count(),
                    "pending_request_count": pending_requests.count(),
                    "active_booking_count": bookings.filter(status__in=active_statuses).count(),
                    "completed_booking_count": bookings.filter(status=Booking.STATUS_COMPLETED).count(),
                    "review_count": reviews.count(),
                    "average_rating": round(float(average_rating), 2),
                    "total_earnings": float(total_earnings),
                    "total_platform_fee": float(total_platform_fee),
                },
                "active_services": ServiceProviderReadSerializer(provider_services, many=True).data,
                "active_bookings": [
                    {
                        "id": booking.id,
                        "service_name": booking.service.name if booking.service else "Service",
                        "customer_name": booking.user.username,
                        "status": booking.status,
                        "location": booking.location,
                        "date": booking.date,
                        "time": booking.time,
                    }
                    for booking in active_bookings
                ],
                "recent_reviews": [
                    {
                        "id": review.id,
                        "rating": review.rating,
                        "comment": review.comment,
                        "created_at": review.created_at,
                        "customer_name": review.customer.username,
                        "service_name": review.provider.service.name,
                    }
                    for review in recent_reviews
                ],
                "recent_payments": [
                    {
                        "id": payment.id,
                        "amount": float(payment.amount),
                        "provider_earnings": float(payment.provider_earnings),
                        "platform_fee": float(payment.platform_fee),
                        "status": payment.status,
                        "created_at": payment.created_at,
                        "service_name": payment.booking.service.name if payment.booking.service else "Service",
                        "customer_name": payment.booking.user.username,
                    }
                    for payment in recent_payments
                ],
                "pending_requests": [
                    {
                        "id": service_request.id,
                        "customer_name": service_request.customer.username,
                        "service_name": service_request.service.name,
                        "location": service_request.location,
                        "date": service_request.date,
                        "time": service_request.time,
                    }
                    for service_request in pending_requests[:5]
                ],
            }
        )


class ServiceProviderView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @staticmethod
    def _parse_service_names(request):
        raw_service_names = request.data.get("service_names")
        if isinstance(raw_service_names, list):
            candidates = raw_service_names
        else:
            raw_value = raw_service_names or request.data.get("service_name") or ""
            normalized = raw_value.replace("\r", "\n").replace(",", "\n")
            candidates = normalized.split("\n")

        service_names = []
        seen = set()
        for candidate in candidates:
            cleaned = str(candidate).strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            service_names.append(cleaned)
        return service_names

    @staticmethod
    def _annotated_queryset():
        active_statuses = ["requested", "assigned", "in_progress"]
        return (
            ServiceProvider.objects.select_related("user", "service", "user__provider_profile")
            .filter(is_active=True)
            .filter(
                Q(user__provider_profile__isnull=True)
                | Q(user__provider_profile__is_active_provider=True)
            )
            .annotate(
                average_rating=Coalesce(Avg("reviews__rating"), Value(0.0)),
                active_jobs=Count(
                    "provider_bookings",
                    filter=Q(provider_bookings__status__in=active_statuses),
                    distinct=True,
                ),
            )
            .order_by("-average_rating", "active_jobs", "price", "-experience")
        )

    def get(self, request):
        providers = self._annotated_queryset()

        service = request.query_params.get("service")
        location = request.query_params.get("location")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        min_rating = request.query_params.get("min_rating")
        user = request.query_params.get("user")
        accepting_jobs = request.query_params.get("accepting_jobs")
        sort_by = request.query_params.get("sort_by")

        if service:
            providers = providers.filter(service_id=service)
        if location:
            providers = providers.filter(location__icontains=location)
        if min_price:
            providers = providers.filter(price__gte=min_price)
        if max_price:
            providers = providers.filter(price__lte=max_price)
        if min_rating:
            providers = providers.filter(average_rating__gte=min_rating)
        if user:
            providers = providers.filter(user_id=user)
        if accepting_jobs == "true":
            providers = providers.filter(user__provider_profile__is_accepting_jobs=True)

        sort_options = {
            "highest_rated": ("-average_rating", "active_jobs", "price", "-experience"),
            "lowest_price": ("price", "-average_rating", "active_jobs"),
            "highest_experience": ("-experience", "-average_rating", "price"),
        }
        if sort_by in sort_options:
            providers = providers.order_by(*sort_options[sort_by])

        serializer = ServiceProviderReadSerializer(providers, many=True)
        return Response(serializer.data)

    def post(self, request):
        service_names = self._parse_service_names(request)
        user = request.user

        if not service_names:
            return Response(
                {"error": "At least one service name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, _ = ProviderProfile.objects.get_or_create(user=user)
        if not profile.is_active_provider or not profile.is_accepting_jobs:
            profile.is_active_provider = True
            profile.is_accepting_jobs = True
            profile.save(update_fields=["is_active_provider", "is_accepting_jobs", "updated_at"])

        created_providers = []
        skipped_services = []
        price = request.data.get("price")
        pricing_type = request.data.get("pricing_type")
        location = request.data.get("location")
        experience = request.data.get("experience", 0)

        for service_name in service_names:
            service, created = Service.objects.get_or_create(
                name=service_name,
                defaults=get_service_defaults(service_name),
            )
            if (
                not created
                and service.name.strip().lower() == "refurbishment"
                and service.pricing_type == Service.PRICING_FIXED
            ):
                service.pricing_type = Service.PRICING_INSPECTION
                service.starting_price = None
                service.save(update_fields=["pricing_type", "starting_price"])
            existing_provider = ServiceProvider.objects.filter(user=user, service=service).first()
            if existing_provider:
                if existing_provider.is_active:
                    skipped_services.append(service.name)
                    continue

                existing_provider.price = price
                existing_provider.pricing_type = pricing_type or service.pricing_type
                existing_provider.experience = experience
                existing_provider.location = location
                existing_provider.is_active = True
                existing_provider.save(
                    update_fields=["price", "pricing_type", "experience", "location", "is_active"]
                )
                created_providers.append(existing_provider)
                continue

            data = {
                "user": user.id,
                "service": service.id,
                "price": price,
                "pricing_type": pricing_type or service.pricing_type,
                "experience": experience,
                "location": location,
                "is_active": True,
            }

            serializer = ServiceProviderSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            created_providers.append(serializer.save())

        if not created_providers:
            return Response(
                {
                    "error": "These services are already registered for this account.",
                    "services": skipped_services,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.role != "professional":
            user.role = "professional"
            user.save(update_fields=["role"])

        created_ids = [provider.id for provider in created_providers]
        read_queryset = self._annotated_queryset().filter(id__in=created_ids)
        read_serializer = ServiceProviderReadSerializer(read_queryset, many=True)
        return Response(
            {
                "message": "Provider services registered successfully.",
                "providers": read_serializer.data,
                "skipped_services": skipped_services,
            },
            status=status.HTTP_201_CREATED,
        )


class ServiceProviderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, provider_id):
        try:
            provider = ServiceProvider.objects.select_related("user", "service").get(id=provider_id)
        except ServiceProvider.DoesNotExist:
            return Response({"error": "Provider service not found."}, status=status.HTTP_404_NOT_FOUND)

        if provider.user_id != request.user.id:
            return Response(
                {"error": "You can only edit your own provider services."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ServiceProviderSerializer(provider, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        updated_provider = serializer.save()
        read_provider = self._read_provider(updated_provider.id)
        return Response(ServiceProviderReadSerializer(read_provider).data)

    def delete(self, request, provider_id):
        try:
            provider = ServiceProvider.objects.get(id=provider_id)
        except ServiceProvider.DoesNotExist:
            return Response({"error": "Provider service not found."}, status=status.HTTP_404_NOT_FOUND)

        if provider.user_id != request.user.id:
            return Response(
                {"error": "You can only change your own provider services."},
                status=status.HTTP_403_FORBIDDEN,
            )

        provider.is_active = False
        provider.save(update_fields=["is_active"])

        return Response(
            {
                "message": f"{provider.service.name} has been removed from your active services.",
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _read_provider(provider_id):
        active_statuses = ["requested", "assigned", "in_progress"]
        return (
            ServiceProvider.objects.select_related("user", "service", "user__provider_profile")
            .annotate(
                average_rating=Coalesce(Avg("reviews__rating"), Value(0.0)),
                active_jobs=Count(
                    "provider_bookings",
                    filter=Q(provider_bookings__status__in=active_statuses),
                    distinct=True,
                ),
            )
            .get(id=provider_id)
        )
