from django import forms
from bevflow.models import Product

class ProductForm(forms.ModelForm):
    image = forms.ImageField(required=True)

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']
