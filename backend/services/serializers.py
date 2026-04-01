# from rest_framework import serializers
# from .models import Service

# class ServiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Service
#         fields = '__all__'


from rest_framework import serializers
from .models import ServiceProvider
from accounts.models import User
from .models import Service

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

# Service Serializer
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']

# Service Provider Serializer
# class ServiceProviderSerializer(serializers.ModelSerializer):
#     user = UserSerializer()
#     service = ServiceSerializer()

#     class Meta:
#         model = ServiceProvider
#         fields = '__all__'

# 👉 This is PERFECT for POST
class ServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = '__all__'

# Nested version for GET
class ServiceProviderReadSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    service = ServiceSerializer()

    class Meta:
        model = ServiceProvider
        fields = '__all__'