

# Create your models here.
    
from django.db import models
from django.conf import settings
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower

class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta:
        constraints = [
            UniqueConstraint(Lower('name'), name='unique_service_name')
        ]
    description = models.TextField()
    # price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class ServiceProvider(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    price = models.IntegerField()
    experience = models.IntegerField(default=0)
    location = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user} - {self.service}"
    

