from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    manufacturer = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)  # ← This must exist
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)
    image_key = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.manufacturer.username}"
