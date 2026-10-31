from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from products.models import Product
from .models import WishlistItem


def wishlist_detail_view(request):
    """Renders the user's saved wishlist catalog."""
    if request.user.is_authenticated:
        saved_products = Product.objects.filter(
            wishlisted_items__user=request.user, 
            is_active=True
        ).select_related('category').prefetch_related('images')
    else:
        wishlist_ids = request.session.get('wishlist', [])
        if isinstance(wishlist_ids, list) and wishlist_ids:
            saved_products = Product.objects.filter(
                id__in=wishlist_ids, 
                is_active=True
            ).select_related('category').prefetch_related('images')
        else:
            saved_products = Product.objects.none()

    context = {
        'products': saved_products,
        'total_saved': saved_products.count(),
    }
    return render(request, 'wishlist/wishlist.html', context)


def toggle_wishlist_view(request, product_id):
    """Toggles a product in/out of the user's wishlist via AJAX or standard POST."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    is_wishlisted = False

    if request.user.is_authenticated:
        item = WishlistItem.objects.filter(user=request.user, product=product).first()
        if item:
            item.delete()
            is_wishlisted = False
            msg = f"Removed {product.name} from your saved items."
        else:
            WishlistItem.objects.create(user=request.user, product=product)
            is_wishlisted = True
            msg = f"Saved {product.name} to your wishlist."
        count = WishlistItem.objects.filter(user=request.user).count()
    else:
        wishlist = request.session.get('wishlist', [])
        if not isinstance(wishlist, list):
            wishlist = []

        if product_id in wishlist:
            wishlist.remove(product_id)
            is_wishlisted = False
            msg = f"Removed {product.name} from your saved items."
        else:
            wishlist.append(product_id)
            is_wishlisted = True
            msg = f"Saved {product.name} to your wishlist."

        request.session['wishlist'] = wishlist
        request.session.modified = True
        count = len(wishlist)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'is_wishlisted': is_wishlisted,
            'wishlist_count': count,
            'message': msg,
        })

    messages.info(request, msg)
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'wishlist:detail')


def remove_from_wishlist_view(request, product_id):
    """Explicitly removes a product from the wishlist."""
    product = get_object_or_404(Product, pk=product_id)

    if request.user.is_authenticated:
        WishlistItem.objects.filter(user=request.user, product=product).delete()
    else:
        wishlist = request.session.get('wishlist', [])
        if isinstance(wishlist, list) and product_id in wishlist:
            wishlist.remove(product_id)
            request.session['wishlist'] = wishlist
            request.session.modified = True

    messages.info(request, f"Removed {product.name} from your wishlist.")
    return redirect('wishlist:detail')
