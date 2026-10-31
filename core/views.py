from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from products.models import Category, Product
from .models import NewsletterSubscriber


def home(request):
    """Homepage view with dynamic categories, featured items, and bestsellers."""
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:4]
    bestseller_products = Product.objects.filter(is_active=True, is_bestseller=True)[:4]
    new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:4]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'bestseller_products': bestseller_products,
        'new_arrivals': new_arrivals,
    }
    return render(request, 'core/index.html', context)


def subscribe_newsletter(request):
    """Subscribes an email to the newsletter."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, 'Please provide a valid email address.')
            return redirect('core:home')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('core:home')

        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created:
            messages.success(request, 'Thank you for subscribing to Cartza updates.')
        else:
            messages.info(request, 'You are already subscribed to Cartza updates.')

    return redirect('core:home')


def custom_404_view(request, exception=None):
    """Custom 404 page adhering to Cartza design system."""
    return render(request, '404.html', status=404)


def about_view(request):
    """Renders the About Cartza brand philosophy and craftsmanship page."""
    return render(request, 'core/about.html', {'active_policy': 'about'})


def shipping_view(request):
    """Renders the Shipping & Delivery policy, rates, and timelines."""
    return render(request, 'core/shipping.html', {'active_policy': 'shipping'})


def returns_view(request):
    """Renders the 7-day Restful Returns & Exchanges process page."""
    return render(request, 'core/returns.html', {'active_policy': 'returns'})


def privacy_view(request):
    """Renders the Privacy Policy and user data governance documentation."""
    return render(request, 'core/privacy.html', {'active_policy': 'privacy'})


def terms_view(request):
    """Renders the Terms & Conditions governing use of the Cartza platform."""
    return render(request, 'core/terms.html', {'active_policy': 'terms'})

