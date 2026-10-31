from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile


class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        required=True, 
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Choose a strong password'}),
        label="Password",
        help_text="Must be at least 8 characters long and contain varied characters."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match.")
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error('password', e)

        return cleaned_data


class ProfileUpdateForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=False, label="First Name")
    last_name = forms.CharField(max_length=50, required=False, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(max_length=15, required=False, label="Phone Number")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="Delivery Address")
    city = forms.CharField(max_length=100, required=False, label="City")
    state = forms.CharField(max_length=100, required=False, label="State")
    pincode = forms.CharField(max_length=6, required=False, label="PIN Code")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing_class} form-control".strip()

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode', '').strip()
        if pincode and (len(pincode) != 6 or not pincode.isdigit()):
            raise ValidationError("Enter a valid 6-digit Indian PIN code.")
        return pincode
