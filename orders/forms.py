from django import forms
from .models import ShippingAddress


class CheckoutForm(forms.ModelForm):
  class Meta:
    model = ShippingAddress
    fields = [
        'full_name',
        'address',
        'city',
        'postal_code',
        'phone',
    ]  
    widgets = {
        'full_name': forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': "Ім'я та Прізвище"}
        ),
        'address': forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Вулиця, будинок, квартира'}
        ),
        'city': forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Місто'}
        ),
        'postal_code': forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Поштовий індекс'}
        ),
        'phone': forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Номер телефону'}
        ),
    }

class CouponApplyForm(forms.Form):
    code = forms.CharField(label='Промокод', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть код'}))