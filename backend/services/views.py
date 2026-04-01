# from django.shortcuts import render

# Create your views here.

#####-----------old code ----------
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Service
from .serializers import ServiceSerializer

class ServiceListView(APIView):
    def get(self, request):
        services = Service.objects.all()
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ServiceSerializer(data=request.data)
        print(request.data)
        print(serializer)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    


#####-----------new code ----------
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ServiceProvider
# from .serializers import ServiceProviderSerializer
from .serializers import ServiceProviderSerializer, ServiceProviderReadSerializer

# class ServiceProviderView(APIView):

#     # ✅ GET → Fetch all providers
#     def get(self, request):
#         providers = ServiceProvider.objects.all()
#         serializer = ServiceProviderSerializer(providers, many=True)
#         return Response(serializer.data)

#     # 🔥 POST → Create provider
#     def post(self, request):
#         serializer = ServiceProviderSerializer(data=request.data)
        
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from accounts.models import User
class ServiceProviderView(APIView):

    def get(self, request):
        providers = ServiceProvider.objects.all()

        # 🔍 Filters
        service = request.query_params.get('service')
        location = request.query_params.get('location')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        user = request.query_params.get('user')

        if service:
            providers = providers.filter(service_id=service)

        if location:
            providers = providers.filter(location__icontains=location)

        if min_price:
            providers = providers.filter(price__gte=min_price)

        if max_price:
            providers = providers.filter(price__lte=max_price)

        if user:
            providers = providers.filter(user_id=user)

        serializer = ServiceProviderReadSerializer(providers, many=True)
        return Response(serializer.data)
    

    # def get(self, request):
    #     providers = ServiceProvider.objects.all()
    #     serializer = ServiceProviderReadSerializer(providers, many=True)  # 🔥 changed
    #     return Response(serializer.data)

    # def post(self, request):
    #     serializer = ServiceProviderSerializer(data=request.data)
        
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        user_id = request.data.get('user')

        user = User.objects.get(id=user_id)

        # 🔥 Restriction logic
        if user.role != 'professional':
            return Response(
                {"error": "Only professionals can register as service providers"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ServiceProviderSerializer(data=request.data)

        if serializer.is_valid():
            provider = serializer.save()

            # return readable data
            read_serializer = ServiceProviderReadSerializer(provider)
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)