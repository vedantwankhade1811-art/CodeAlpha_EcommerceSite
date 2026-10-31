def cart_context(request):
    """Provides cart item count and summary for templates."""
    # In Phase 1, we read cart from session if available, else 0
    cart = request.session.get('cart', {})
    cart_count = sum(item.get('quantity', 0) for item in cart.values()) if isinstance(cart, dict) else 0
    return {
        'cart_count': cart_count,
    }
