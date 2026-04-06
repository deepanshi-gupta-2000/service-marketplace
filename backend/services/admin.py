from django.contrib import admin

from .models import ProviderProfile, Service, ServiceProvider


admin.site.register(Service)
admin.site.register(ProviderProfile)
admin.site.register(ServiceProvider)
