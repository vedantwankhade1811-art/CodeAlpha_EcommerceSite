import json
import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.db import transaction
from django.conf import settings

from products.models import Product
from cart.views import calculate_coupon_discount
from .models import Order, OrderItem
from .forms import CheckoutForm
from .services import RazorpayService

logger = logging.getLogger(__name__)


def checkout_view(request):
    """
    Processes user checkout, validates shipping data, creates application order
    with appropriate pending/confirmed status, and routes to payment processing or COD confirmation.
    """
    # Ensure user is authenticated before proceeding to checkout
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in or create an account to proceed with checkout.")
        return redirect(f"{reverse('accounts:login')}?next={reverse('orders:checkout')}")

    cart = request.session.get('cart', {})
    if not isinstance(cart, dict) or not cart:
        messages.warning(request, "Your shopping bag is empty. Please add items before checking out.")
        return redirect('products:shop')

    cart_items = []
    subtotal = Decimal('0.00')

    for key, item in list(cart.items()):
        try:
            prod = Product.objects.filter(pk=item['product_id'], is_active=True).first()
            if not prod:
                del cart[key]
                continue
            qty = int(item['quantity'])
            price = Decimal(str(item['price']))
            line_total = price * qty
            subtotal += line_total
            cart_items.append({
                'key': key,
                'product': prod,
                'product_name': item.get('product_name', prod.name),
                'product_slug': item.get('product_slug', prod.slug),
                'price': price,
                'quantity': qty,
                'size': item.get('size', ''),
                'color': item.get('color', ''),
                'image_url': prod.image.url if (prod.image and bool(prod.image)) else (prod.primary_image.image.url if (prod.primary_image and getattr(prod.primary_image, 'image', None) and bool(prod.primary_image.image)) else item.get('image_url', '/static/images/placeholder.svg')),
                'line_total': line_total,
            })
        except Exception:
            continue

    if not cart_items:
        request.session['cart'] = {}
        request.session.modified = True
        messages.warning(request, "Items in your shopping bag are no longer available.")
        return redirect('products:shop')

    # Coupon code handling
    coupon = request.session.get('coupon')
    coupon_code = coupon.get('code') if isinstance(coupon, dict) else None
    discount, promo_free_shipping = calculate_coupon_discount(coupon_code, subtotal)

    # Shipping rules: Free for >= ₹999 or promo override, else ₹79
    shipping = Decimal('0.00') if (subtotal >= Decimal('999.00') or promo_free_shipping) else Decimal('79.00')
    grand_total = max(Decimal('0.00'), subtotal - discount + shipping)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.subtotal = subtotal
                order.shipping_fee = shipping
                order.grand_total = grand_total
                if coupon_code:
                    order.notes = f"Promo '{coupon_code}' (-₹{discount}): {order.notes}".strip(': ')

                # Set initial payment status based on chosen method
                if order.payment_method == 'cod':
                    order.is_paid = False
                    order.payment_status = 'pending_cod'
                    order.status = 'confirmed'
                else:  # UPI or Card
                    # NEVER simulate payment success. Mark pending until verified.
                    order.is_paid = False
                    order.payment_status = 'pending'
                    order.status = 'pending_payment'

                order.save()

                # Create OrderItems
                for item in cart_items:
                    prod = item['product']
                    OrderItem.objects.create(
                        order=order,
                        product=prod,
                        product_name=item['product_name'],
                        product_slug=item['product_slug'],
                        price=item['price'],
                        quantity=item['quantity'],
                        size=item['size'],
                        color=item['color'],
                        image_url=item['image_url'],
                        line_total=item['line_total'],
                    )
                    # For COD, decrement stock immediately
                    if order.payment_method == 'cod' and prod:
                        prod.stock = max(0, prod.stock - item['quantity'])
                        prod.save(update_fields=['stock'])

                # Save address to profile if profile address is blank
                profile = getattr(request.user, 'profile', None)
                if profile and not profile.address:
                    profile.phone = order.phone
                    profile.address = order.address
                    profile.city = order.city
                    profile.state = order.state
                    profile.pincode = order.pincode
                    profile.save()

                if order.payment_method == 'cod':
                    # Clear session cart for COD
                    request.session['cart'] = {}
                    if 'coupon' in request.session:
                        del request.session['coupon']
                    request.session.modified = True

                    messages.success(request, f"Order #{order.order_number} confirmed! Cash on Delivery scheduled.")
                    return redirect('orders:confirmation', order_number=order.order_number)
                else:
                    # Online Payment: Create Razorpay order if configured
                    if RazorpayService.is_configured():
                        try:
                            RazorpayService.create_razorpay_order(order)
                        except Exception as e:
                            logger.error("Razorpay order creation error: %s", e)
                            order.payment_error_reason = f"Gateway initialization error: {str(e)}"
                            order.save(update_fields=['payment_error_reason'])

                    # Redirect to dedicated payment screen
                    return redirect('orders:payment_process', order_number=order.order_number)
        else:
            messages.error(request, "Please review the highlighted shipping and contact details.")
    else:
        profile = getattr(request.user, 'profile', None)
        initial_data = {
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'phone': getattr(profile, 'phone', '') if profile else '',
            'address': getattr(profile, 'address', '') if profile else '',
            'city': getattr(profile, 'city', '') if profile else '',
            'state': getattr(profile, 'state', '') if profile else '',
            'pincode': getattr(profile, 'pincode', '') if profile else '',
            'payment_method': 'cod',
        }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount': discount,
        'coupon_code': coupon_code,
        'shipping': shipping,
        'grand_total': grand_total,
        'total_items': sum(i['quantity'] for i in cart_items),
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def payment_process_view(request, order_number):
    """
    Renders the Razorpay payment gateway integration screen.
    Handles online payment processing for UPI, Credit/Debit cards.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.is_paid:
        messages.info(request, "This order has already been verified and paid.")
        return redirect('orders:confirmation', order_number=order.order_number)

    if order.payment_method == 'cod':
        return redirect('orders:confirmation', order_number=order.order_number)

    is_configured = RazorpayService.is_configured()

    # If Razorpay is configured but no order ID yet created, generate one now
    if is_configured and not order.razorpay_order_id:
        try:
            RazorpayService.create_razorpay_order(order)
        except Exception as e:
            logger.error("Failed to create Razorpay order in payment_process: %s", e)
            order.payment_error_reason = str(e)
            order.save(update_fields=['payment_error_reason'])

    context = {
        'order': order,
        'items': order.items.all(),
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
        'razorpay_order_id': order.razorpay_order_id,
        'is_configured': is_configured,
        'amount_in_paise': order.amount_in_paise,
    }
    return render(request, 'orders/payment_process.html', context)


@login_required
@require_POST
def payment_verify_view(request):
    """
    Cryptographically verifies Razorpay payment signature server-side.
    Only marks an order as PAID upon valid signature match.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    order_number = data.get('order_number')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not order_number or not razorpay_payment_id:
        return JsonResponse({'status': 'error', 'message': 'Missing payment verification details.'}, status=400)

    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Guard against duplicate verification
    if order.is_paid:
        return JsonResponse({
            'status': 'success',
            'message': 'Order is already verified.',
            'redirect_url': reverse('orders:confirmation', kwargs={'order_number': order.order_number})
        })

    # Verify cryptographic HMAC signature
    is_valid = RazorpayService.verify_signature(
        razorpay_order_id=razorpay_order_id or order.razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature
    )

    if is_valid:
        with transaction.atomic():
            order.is_paid = True
            order.status = 'confirmed'
            order.payment_status = 'paid'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.payment_error_reason = ''
            order.save()

            # Decrement inventory upon verified payment
            for item in order.items.all():
                if item.product:
                    item.product.stock = max(0, item.product.stock - item.quantity)
                    item.product.save(update_fields=['stock'])

            # Clear session cart and used coupon
            request.session['cart'] = {}
            if 'coupon' in request.session:
                del request.session['coupon']
            request.session.modified = True

        messages.success(request, f"Payment verified! Order #{order.order_number} confirmed.")
        return JsonResponse({
            'status': 'success',
            'message': 'Payment successfully verified.',
            'redirect_url': reverse('orders:confirmation', kwargs={'order_number': order.order_number})
        })
    else:
        # Invalid signature: reject and mark failure
        order.payment_status = 'failed'
        order.status = 'payment_failed'
        order.payment_error_reason = 'Invalid payment cryptographic signature verification.'
        order.save(update_fields=['payment_status', 'status', 'payment_error_reason'])

        logger.warning("Payment signature verification failed for order %s", order.order_number)
        return JsonResponse({
            'status': 'error',
            'message': 'Payment verification failed: Invalid digital signature. Your account has not been debited.',
        }, status=400)


@login_required
@require_POST
def payment_failed_view(request):
    """
    Handles payment failure or user cancellation callbacks from Razorpay modal.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    order_number = data.get('order_number')
    error_desc = data.get('description', 'Payment cancelled or dismissed by customer.')

    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if not order.is_paid:
        order.payment_status = 'failed'
        order.status = 'payment_failed'
        order.payment_error_reason = error_desc
        order.save(update_fields=['payment_status', 'status', 'payment_error_reason'])

    return JsonResponse({
        'status': 'recorded',
        'retry_url': reverse('orders:payment_retry', kwargs={'order_number': order.order_number})
    })


@login_required
def payment_retry_view(request, order_number):
    """
    Safely initiates a payment retry for pending or failed orders without losing customer data.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.is_paid:
        messages.info(request, "This order is already paid.")
        return redirect('orders:confirmation', order_number=order.order_number)

    # Check stock availability
    for item in order.items.all():
        if item.product and item.product.stock < item.quantity:
            messages.error(request, f"Item '{item.product_name}' is currently out of stock.")
            return redirect('orders:detail', order_number=order.order_number)

    # Reset status to pending_payment
    order.status = 'pending_payment'
    order.payment_status = 'pending'
    order.payment_error_reason = ''
    order.save(update_fields=['status', 'payment_status', 'payment_error_reason'])

    # Recreate or refresh Razorpay order if configured
    if RazorpayService.is_configured():
        try:
            RazorpayService.create_razorpay_order(order)
        except Exception as e:
            logger.error("Razorpay order recreation error: %s", e)

    return redirect('orders:payment_process', order_number=order.order_number)


@csrf_exempt
@require_POST
def payment_webhook_view(request):
    """
    Asynchronous server-to-server webhook endpoint for Razorpay events.
    Verifies X-Razorpay-Signature and updates orders idempotently.
    """
    webhook_signature = request.headers.get('X-Razorpay-Signature', '')
    payload_body = request.body

    if not RazorpayService.verify_webhook_signature(payload_body, webhook_signature):
        return HttpResponseBadRequest("Invalid webhook signature")

    try:
        event = json.loads(payload_body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON payload")

    event_type = event.get('event')
    payload = event.get('payload', {})
    payment_entity = payload.get('payment', {}).get('entity', {})
    rzp_order_id = payment_entity.get('order_id')
    rzp_payment_id = payment_entity.get('id')

    if not rzp_order_id:
        return HttpResponse(status=200)

    order = Order.objects.filter(razorpay_order_id=rzp_order_id).first()
    if not order:
        return HttpResponse(status=200)

    if event_type == 'payment.captured':
        if not order.is_paid:
            with transaction.atomic():
                order.is_paid = True
                order.status = 'confirmed'
                order.payment_status = 'paid'
                order.razorpay_payment_id = rzp_payment_id
                order.payment_error_reason = ''
                order.save()

                for item in order.items.all():
                    if item.product:
                        item.product.stock = max(0, item.product.stock - item.quantity)
                        item.product.save(update_fields=['stock'])
    elif event_type == 'payment.failed':
        if not order.is_paid:
            order.status = 'payment_failed'
            order.payment_status = 'failed'
            order.payment_error_reason = payment_entity.get('error_description', 'Webhook reported payment failure.')
            order.save()

    return HttpResponse(status=200)


def order_confirmation_view(request, order_number):
    """Renders the order confirmation and receipt screen."""
    order = get_object_or_404(Order, order_number=order_number)

    if order.user and request.user.is_authenticated and order.user != request.user and not request.user.is_staff:
        messages.error(request, "You do not have access to view this order confirmation.")
        return redirect('core:home')

    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'orders/confirmation.html', context)


@login_required
def order_list_view(request):
    """Lists order history for the authenticated user."""
    orders = request.user.orders.all()
    return render(request, 'orders/history.html', {'orders': orders})


@login_required
def order_detail_view(request, order_number):
    """Displays tracking and item breakdown for an individual order."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/detail.html', {'order': order, 'items': order.items.all()})
