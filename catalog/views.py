from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category

def product_list(request):
    category_slug = request.GET.get('category')
    query = request.GET.get('q', '').strip()

    products = Product.objects.select_related('category').prefetch_related('images').all()
    categories = Category.objects.all()

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if query:
        words = query.split()
        for word in words:
            products = products.filter(
                Q(title__icontains=word) |
                Q(category__title__icontains=word)
            )

    return render(request, 'catalog/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'query': query,
    })

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        slug=slug
    )
    return render(request, 'catalog/product_detail.html', {
        'product': product,
    })