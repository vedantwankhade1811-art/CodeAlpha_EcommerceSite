from .models import Category

def categories_context(request):
    """Provides all categories for navigation headers and dropdowns."""
    try:
        categories = Category.objects.all()
    except Exception:
        categories = []
    return {
        'nav_categories': categories,
    }
