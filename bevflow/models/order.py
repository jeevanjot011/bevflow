from django.db import models
from django.contrib.auth.models import User
from bevflow.models.product import Product


class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        default="PENDING",
        choices=[
            ("PENDING", "Pending"),
            ("ACCEPTED", "Accepted"),
            ("REJECTED", "Rejected"),
            ("DELIVERED", "Delivered"),
        ],
    )

    def __str__(self):
        return f"Order #{self.id} - {self.product.name}"
