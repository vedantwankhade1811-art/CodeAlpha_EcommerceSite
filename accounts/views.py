from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, ProfileUpdateForm
from .models import Profile


def _sync_session_wishlist(request, user):
    """Transfers any guest items saved in session wishlist into user database records upon login."""
    session_wishlist = request.session.get('wishlist', [])
    if isinstance(session_wishlist, list) and session_wishlist:
        try:
            from wishlist.models import WishlistItem
            from products.models import Product
            for product_id in session_wishlist:
                prod = Product.objects.filter(pk=product_id, is_active=True).first()
                if prod:
                    WishlistItem.objects.get_or_create(user=user, product=prod)
            request.session['wishlist'] = []
            request.session.modified = True
        except Exception:
            pass


def register_view(request):
    """Handles new user registration with strict validation."""
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    next_url = request.POST.get('next') or request.GET.get('next', 'accounts:profile')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            messages.success(request, f"Welcome to Cartza, {user.username}! Your account has been created.")
            login(request, user)
            _sync_session_wishlist(request, user)
            return redirect(next_url if next_url != 'accounts:profile' else 'accounts:profile')
        else:
            messages.error(request, "Please resolve the errors below to create your account.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'next': next_url})


def login_view(request):
    """Handles user sign in with username or email."""
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    next_url = request.GET.get('next', 'core:home')

    if request.method == 'POST':
        login_id = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Allow login via username or email
        user = authenticate(request, username=login_id, password=password)
        if user is None and '@' in login_id:
            try:
                user_obj = User.objects.get(email__iexact=login_id)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user is not None:
            if user.is_active:
                login(request, user)
                _sync_session_wishlist(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect(next_url if next_url != 'core:home' else 'core:home')
            else:
                messages.error(request, "This account is currently disabled.")
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'accounts/login.html', {'next': next_url})


def logout_view(request):
    """Logs the user out and redirects to home."""
    logout(request)
    messages.info(request, "You have been securely signed out.")
    return redirect('core:home')


@login_required
def profile_view(request):
    """Displays user profile, personal details, and default addresses."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': profile,
    })


@login_required
def profile_edit_view(request):
    """Allows user to update personal details and delivery addresses."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST)
        if form.is_valid():
            # Update User instance
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            new_email = form.cleaned_data['email'].strip().lower()

            if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                messages.error(request, "This email address is already in use by another account.")
                return render(request, 'accounts/profile_edit.html', {'form': form})

            request.user.email = new_email
            request.user.save()

            # Update Profile instance
            profile.phone = form.cleaned_data['phone']
            profile.address = form.cleaned_data['address']
            profile.city = form.cleaned_data['city']
            profile.state = form.cleaned_data['state']
            profile.pincode = form.cleaned_data['pincode']
            profile.save()

            messages.success(request, "Your profile details have been successfully updated.")
            return redirect('accounts:profile')
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': profile.phone,
            'address': profile.address,
            'city': profile.city,
            'state': profile.state,
            'pincode': profile.pincode,
        }
        form = ProfileUpdateForm(initial=initial_data)

    return render(request, 'accounts/profile_edit.html', {'form': form})
