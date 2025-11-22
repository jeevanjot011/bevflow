from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('manufacturer', 'Manufacturer'),
        ('customer', 'Customer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    area_code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
