from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from products.models import Product


def cart_detail_view(request):
    """Renders the shopping cart page with dynamic totals, shipping rules, and item listings."""
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

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
            img_url = item.get('image_url', '')
            if prod.image and bool(prod.image):
                img_url = prod.image.url
            elif prod.primary_image and hasattr(prod.primary_image, 'image') and bool(prod.primary_image.image):
                img_url = prod.primary_image.image.url
            elif not img_url:
                img_url = '/static/images/placeholder.svg'
            item['image_url'] = img_url

            cart_items.append({
                'key': key,
                'product': prod,
                'product_name': item.get('product_name', prod.name),
                'product_slug': item.get('product_slug', prod.slug),
                'price': price,
                'quantity': qty,
                'size': item.get('size', ''),
                'color': item.get('color', ''),
                'image_url': img_url,
                'line_total': line_total,
                'max_stock': prod.stock,
            })
        except Exception:
            continue

    request.session['cart'] = cart
    request.session.modified = True

    # Coupon code handling
    coupon = request.session.get('coupon')
    coupon_code = coupon.get('code') if isinstance(coupon, dict) else None
    discount, promo_free_shipping = calculate_coupon_discount(coupon_code, subtotal)

    # Free shipping on orders >= ₹999 or promo override, else ₹79 (or ₹0 if empty)
    if subtotal == Decimal('0.00'):
        shipping = Decimal('0.00')
    elif subtotal >= Decimal('999.00') or promo_free_shipping:
        shipping = Decimal('0.00')
    else:
        shipping = Decimal('79.00')

    grand_total = max(Decimal('0.00'), subtotal - discount + shipping)
    needed_for_free_shipping = Decimal('0.00') if promo_free_shipping else max(Decimal('0.00'), Decimal('999.00') - subtotal)

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount': discount,
        'coupon_code': coupon_code,
        'shipping': shipping,
        'grand_total': grand_total,
        'needed_for_free_shipping': needed_for_free_shipping,
        'total_items': sum(item['quantity'] for item in cart_items),
    }
    return render(request, 'cart/cart.html', context)


def calculate_coupon_discount(coupon_code, subtotal):
    """Calculates discount and shipping override based on valid coupon codes."""
    code = (coupon_code or '').strip().upper()
    discount = Decimal('0.00')
    free_shipping = False

    if code == 'CARTZA15':
        discount = (subtotal * Decimal('0.15')).quantize(Decimal('0.01'))
    elif code == 'CARTZA':
        discount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
        free_shipping = True
    elif code == 'WELCOME10':
        discount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))

    return discount, free_shipping


def apply_coupon_view(request):
    """Applies a promotion voucher code to the cart session."""
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        if code in ['CARTZA15', 'CARTZA', 'WELCOME10']:
            request.session['coupon'] = {'code': code}
            request.session.modified = True
            messages.success(request, f"Promo code '{code}' applied to your shopping bag!")
        else:
            messages.error(request, f"'{code}' is not a valid promo voucher.")
    return redirect('cart:detail')


def remove_coupon_view(request):
    """Removes an active coupon code from the cart session."""
    if 'coupon' in request.session:
        del request.session['coupon']
        request.session.modified = True
        messages.info(request, "Promo code has been removed.")
    return redirect('cart:detail')


def add_to_cart_view(request, product_id):
    """Adds a product to the session cart with quantity and option validation."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
        quantity = max(1, quantity)

        selected_size = request.POST.get('selected_size', '').strip()
        selected_color = request.POST.get('selected_color', '').strip()
        buy_now = request.POST.get('buy_now', '0') == '1'

        # Check stock limits
        if product.stock <= 0:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'{product.name} is currently sold out.'}, status=400)
            messages.error(request, f"{product.name} is currently sold out.")
            return redirect(product.get_absolute_url())

        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {}

        # Formulate unique item key based on product + selected variations
        safe_size = selected_size.replace('/', '-').replace(' ', '-')
        safe_color = selected_color.replace('/', '-').replace(' ', '-')
        key_parts = [str(product.id)]
        if safe_size:
            key_parts.append(safe_size)
        if safe_color:
            key_parts.append(safe_color)
        item_key = "_".join(key_parts)

        current_qty = cart.get(item_key, {}).get('quantity', 0)
        new_qty = current_qty + quantity

        if new_qty > product.stock:
            new_qty = product.stock
            msg = f"Added to cart (capped at available stock of {product.stock} units)."
        else:
            msg = f"Added {product.name} to your shopping bag."

        image_url = '/static/images/placeholder.svg'
        try:
            if product.image and bool(product.image):
                image_url = product.image.url
            elif product.primary_image and bool(product.primary_image.image):
                image_url = product.primary_image.image.url
        except Exception:
            image_url = '/static/images/placeholder.svg'

        cart[item_key] = {
            'product_id': product.id,
            'product_name': product.name,
            'product_slug': product.slug,
            'price': str(product.price),
            'quantity': new_qty,
            'size': selected_size,
            'color': selected_color,
            'image_url': image_url,
        }

        request.session['cart'] = cart
        request.session.modified = True

        total_items = sum(item.get('quantity', 0) for item in cart.values())

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': msg,
                'cart_count': total_items,
                'redirect_url': reverse('cart:detail') if buy_now else None,
            })

        messages.success(request, msg)
        return redirect('cart:detail')

    return redirect(product.get_absolute_url())


def update_cart_view(request, item_key):
    """Updates quantity of an item in the cart."""
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = request.session.get('cart', {})
        if isinstance(cart, dict) and item_key in cart:
            prod_id = cart[item_key]['product_id']
            prod = Product.objects.filter(pk=prod_id).first()
            max_stock = prod.stock if prod else 99

            if action == 'increase':
                if cart[item_key]['quantity'] < max_stock:
                    cart[item_key]['quantity'] += 1
                else:
                    messages.warning(request, f"Maximum available stock for this item is {max_stock}.")
            elif action == 'decrease':
                cart[item_key]['quantity'] -= 1
                if cart[item_key]['quantity'] <= 0:
                    del cart[item_key]
            elif action == 'set':
                try:
                    qty = int(request.POST.get('quantity', 1))
                    if qty > 0:
                        cart[item_key]['quantity'] = min(qty, max_stock)
                    else:
                        del cart[item_key]
                except ValueError:
                    pass

            request.session['cart'] = cart
            request.session.modified = True

    return redirect('cart:detail')


def remove_from_cart_view(request, item_key):
    """Removes an item completely from the cart."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if isinstance(cart, dict) and item_key in cart:
            name = cart[item_key].get('product_name', 'Item')
            del cart[item_key]
            request.session['cart'] = cart
            request.session.modified = True
            messages.info(request, f"Removed {name} from your shopping bag.")
    return redirect('cart:detail')


def clear_cart_view(request):
    """Clears all items from the shopping cart."""
    if request.method == 'POST':
        request.session['cart'] = {}
        request.session.modified = True
        messages.info(request, "Your shopping cart has been cleared.")
    return redirect('cart:detail')
