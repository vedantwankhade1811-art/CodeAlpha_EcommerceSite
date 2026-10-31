from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'full_name',
            'email',
            'phone',
            'address',
            'city',
            'state',
            'pincode',
            'payment_method',
            'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit mobile number',
                'required': True,
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Flat / House No., Building Name, Street / Locality',
                'required': True,
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City / Town',
                'required': True,
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State',
                'required': True,
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '6-digit PIN code',
                'required': True,
            }),
            'payment_method': forms.RadioSelect(attrs={
                'class': 'payment-radio-input',
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional delivery remarks (e.g., Leave with security)',
            }),
        }
