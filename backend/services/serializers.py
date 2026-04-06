from django.db.models import Avg, Value
from django.db.models.functions import Coalesce
from accounts.models import User
from rest_framework import serializers

from .models import ProviderProfile, Service, ServiceProvider


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]


class ServiceSerializer(serializers.ModelSerializer):
    pricing_type_label = serializers.CharField(source="get_pricing_type_display", read_only=True)
    pricing_display = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "pricing_type",
            "pricing_type_label",
            "starting_price",
            "pricing_display",
        ]

    def get_pricing_display(self, obj):
        if obj.pricing_type == Service.PRICING_FIXED and obj.starting_price is not None:
            return f"Rs. {obj.starting_price}"
        if obj.pricing_type == Service.PRICING_STARTING_FROM and obj.starting_price is not None:
            return f"Starts at Rs. {obj.starting_price}"
        if obj.pricing_type == Service.PRICING_INSPECTION:
            return "Inspection required before final quote"
        if obj.pricing_type == Service.PRICING_CUSTOM_QUOTE:
            return "Custom quote after requirements review"
        return obj.get_pricing_type_display()


class ProviderProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProviderProfile
        fields = [
            "id",
            "user",
            "display_name",
            "bio",
            "skills_summary",
            "availability_notes",
            "default_location",
            "available_from",
            "available_to",
            "is_accepting_jobs",
            "is_active_provider",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class ServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = "__all__"


class ServiceProviderReadSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    service = ServiceSerializer()
    provider_profile = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    active_jobs = serializers.SerializerMethodField()
    pricing_type_label = serializers.CharField(source="get_pricing_type_display", read_only=True)
    pricing_display = serializers.SerializerMethodField()

    class Meta:
        model = ServiceProvider
        fields = [
            "id",
            "user",
            "service",
            "price",
            "pricing_type",
            "pricing_type_label",
            "pricing_display",
            "experience",
            "location",
            "is_active",
            "provider_profile",
            "average_rating",
            "active_jobs",
        ]

    def get_provider_profile(self, obj):
        profile = getattr(obj.user, "provider_profile", None)
        if not profile:
            return None
        return ProviderProfileSerializer(profile).data

    def get_average_rating(self, obj):
        if hasattr(obj, "average_rating"):
            return round(float(obj.average_rating or 0), 2)

        reviews_manager = getattr(obj, "reviews", None)
        if reviews_manager is None:
            return 0.0

        aggregate = reviews_manager.aggregate(value=Coalesce(Avg("rating"), Value(0.0)))
        return round(float(aggregate["value"] or 0), 2)

    def get_active_jobs(self, obj):
        if hasattr(obj, "active_jobs"):
            return int(obj.active_jobs or 0)

        bookings_manager = getattr(obj, "provider_bookings", None)
        if bookings_manager is None:
            return 0

        return bookings_manager.filter(status__in=["requested", "assigned", "in_progress"]).count()

    def get_pricing_display(self, obj):
        if obj.pricing_type == Service.PRICING_FIXED and obj.price is not None:
            return f"Rs. {obj.price}"
        if obj.pricing_type == Service.PRICING_STARTING_FROM and obj.price is not None:
            return f"Starts at Rs. {obj.price}"
        if obj.pricing_type == Service.PRICING_INSPECTION:
            return "Inspection required before final quote"
        if obj.pricing_type == Service.PRICING_CUSTOM_QUOTE:
            return "Custom quote after requirements review"
        return obj.get_pricing_type_display()
