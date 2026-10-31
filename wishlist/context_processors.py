def wishlist_context(request):
    """Provides wishlist item count and wishlisted product IDs for templates."""
    if request.user.is_authenticated:
        from .models import WishlistItem
        items = WishlistItem.objects.filter(user=request.user)
        wishlist_count = items.count()
        wishlist_product_ids = list(items.values_list('product_id', flat=True))
    else:
        wishlist = request.session.get('wishlist', [])
        if isinstance(wishlist, list):
            wishlist_count = len(wishlist)
            wishlist_product_ids = wishlist
        else:
            wishlist_count = 0
            wishlist_product_ids = []

    return {
        'wishlist_count': wishlist_count,
        'wishlist_product_ids': wishlist_product_ids,
    }
