from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from bevflow.forms import ProductForm
from bevflow.models import Product
from bevflow.aws.s3 import upload_image

@login_required
def manufacturer_dashboard(request):
    return render(request, 'bevflow/manufacturer_dashboard.html')

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.manufacturer = request.user

            image_file = request.FILES['image']
            image_key = image_file.name
            image_url = upload_image(image_file, image_key)

            product.image_key = image_key
            product.image_url = image_url

            product.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'bevflow/product_create.html', {'form': form})


@login_required
def product_list(request):
    products = Product.objects.filter(manufacturer=request.user)
    return render(request, 'bevflow/product_list.html', {'products': products})

@login_required
def order_success(request):
    return render(request, 'bevflow/order_success.html')
