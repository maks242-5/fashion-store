from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Category, Product


def _safe_cache_get(key):
    try:
        return cache.get(key)
    except Exception:
        return None


def _safe_cache_set(key, value, timeout=300):
    try:
        cache.set(key, value, timeout=timeout)
    except Exception:
        pass


def _get_base_products():
    products = _safe_cache_get('catalog_products_base')
    if products is None:
        products = list(
            Product.objects.filter(is_active=True)
            .select_related('category')
            .prefetch_related('images')
            .order_by('-created_at')
        )
        _safe_cache_set('catalog_products_base', products, timeout=300)
    return products


def product_list(request):
    category_slug = request.GET.get('category', '').strip()
    query = request.GET.get('q', '').strip()

    categories = _safe_cache_get('catalog_categories')
    if categories is None:
        categories = list(Category.objects.all())
        _safe_cache_set('catalog_categories', categories, timeout=600)

    products = _get_base_products()

    if category_slug:
        products = [
            p for p in products
            if p.category and (
                p.category.slug == category_slug
                or str(p.category.id) == category_slug
            )
        ]

    if query:
        words = query.lower().split()
        for word in words:
            products = [
                p for p in products
                if (p.title and word in p.title.lower())
                or (p.category and p.category.title and word in p.category.title.lower())
            ]

    return render(request, 'catalog/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'query': query,
    })


def search_suggestions(request):
    q = request.GET.get('q', '').strip().lower()
    if len(q) < 2:
        return JsonResponse({'results': []})

    products = _get_base_products()
    matched = []
    for p in products:
        title_match = p.title and q in p.title.lower()
        cat_match = p.category and p.category.title and q in p.category.title.lower()
        if title_match or cat_match:
            img = p.images.first()
            matched.append({
                'title': p.title,
                'category': p.category.title if p.category else '',
                'price': str(p.price),
                'url': f'/product/{p.slug}/',
                'image': img.image.url if img and img.image else '',
            })
        if len(matched) >= 8:
            break

    return JsonResponse({'results': matched})


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.filter(is_active=True).select_related('category').prefetch_related('images'),
        slug=slug
    )
    return render(request, 'catalog/product_detail.html', {
        'product': product,
    })


def home_view(request):
    featured_products = _safe_cache_get('catalog_featured_products')
    if featured_products is None:
        featured_products = list(
            Product.objects.filter(is_active=True, stock_quantity__gt=0)
            .select_related('category')
            .prefetch_related('images')
            .order_by('-created_at')[:8]
        )
        _safe_cache_set('catalog_featured_products', featured_products, timeout=300)

    return render(request, 'catalog/index.html', {
        'featured_products': featured_products,
    })