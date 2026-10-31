from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import Http404
from .models import Category, Product


def shop_view(request, category_slug=None):
    """
    Shop catalog view with full search, category filtering, 
    price range filtering, sorting, and pagination.
    Supports direct route category_slug and query param ?category=slug.
    """
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    categories = Category.objects.all()

    # Search filter
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Category filter
    selected_category_slug = (category_slug or request.GET.get('category', '')).strip()
    current_category = None
    if selected_category_slug:
        current_category = Category.objects.filter(slug=selected_category_slug).first()
        if current_category:
            queryset = queryset.filter(category=current_category)

    # Price range filter
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Sorting
    sort = request.GET.get('sort', 'newest').strip()
    if sort == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort == 'popularity':
        queryset = queryset.order_by('-is_bestseller', '-is_featured', '-created_at')
    else:  # newest by default
        queryset = queryset.order_by('-created_at')

    # Pagination: 8 items per page for clean desktop 4-col / tablet 3-col display
    paginator = Paginator(queryset, 8)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)

    # Build query string for pagination links preserving existing filters
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    filter_params = params.urlencode()

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'current_category': current_category,
        'selected_category_slug': selected_category_slug,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'filter_params': filter_params,
        'total_count': queryset.count(),
    }
    return render(request, 'products/shop.html', context)


def category_direct_view(request, category_slug):
    """
    Direct friendly category URL handler (e.g. /accessories/, /shoes/, /lifestyle/).
    Matches registered categories or raises standard 404.
    """
    category = Category.objects.filter(slug=category_slug).first()
    if not category:
        raise Http404(f"Category '{category_slug}' does not exist.")
    return shop_view(request, category_slug=category_slug)


def product_detail_view(request, slug):
    """
    Product detail page displaying gallery, pricing, stock, 
    specs, options, and related items.
    """
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'), 
        slug=slug, 
        is_active=True
    )

    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'products/detail.html', context)
