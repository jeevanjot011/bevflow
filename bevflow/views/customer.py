from django.shortcuts import render, redirect, get_object_or_404
from bevflow.models.order import Order
from bevflow.models.product import Product
from bevflow.aws.s3 import generate_presigned_url
from bevflow.aws.messaging import send_order_to_sqs_and_sns
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from bevflow.aws.messaging import send_order_to_sqs_and_sns


@login_required
def customer_home(request):
    products = Product.objects.all()

    product_data = []
    for p in products:
        image_url = generate_presigned_url(p.image_key)
        product_data.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "description": p.description,
            "image": image_url,
        })

    return render(request, "bevflow/customer_home.html", {"products": product_data})

@login_required
def order_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity"))

        order = Order.objects.create(
            customer=request.user,
            product=product,
            quantity=quantity
        )

        # build payload for AWS
        payload = {
            "order_id": order.id,
            "product_id": product.id,
            "product_name": product.name,
            "quantity": order.quantity,
            "customer_id": request.user.id,
            "customer_username": request.user.username,
            "customer_area_code": request.user.userprofile.area_code,
            "manufacturer_id": product.manufacturer.id,
            "manufacturer_username": product.manufacturer.username,
            "manufacturer_email": product.manufacturer.email,
            "manufacturer_area_code": product.manufacturer.userprofile.area_code,
            "created_at": timezone.now().isoformat()
        }

        # This function pushes to SQS and SNS
        send_order_to_sqs_and_sns(payload)

        return redirect("order_success")

    image_url = generate_presigned_url(product.image_key)

    return render(request, "bevflow/order_create.html", {
        "product": product,
        "image": image_url
    })
