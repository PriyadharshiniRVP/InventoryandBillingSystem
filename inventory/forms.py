from django import forms
from .models import Bill, Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock']

class BillItemForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.filter(stock__gt=0))
    quantity = forms.IntegerField(min_value=1)
class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['customer_name', 'customer_mobile', 'customer_address', 'project_manager', ...]
        widgets = {
            'project_manager': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Project Manager(s), comma separated'})
        }
