from django.urls import path
from .views import (
    login_view,
    logout_view,
    customer_home,
    manufacturer_dashboard,
    product_create,
    product_list,
    order_success,
    order_create,
)

urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('customer/home/', customer_home, name='customer_home'),
    path('manufacturer/dashboard/', manufacturer_dashboard, name='manufacturer_dashboard'),
    path('manufacturer/product/create/', product_create, name='product_create'),
    path('products/', product_list, name='product_list'),
    path('order/success/', order_success, name='order_success'),
    path("order/<int:product_id>/", order_create, name="order_create"),
]
