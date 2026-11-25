from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Category, Product

CATALOG_CACHE_KEYS = [
    'catalog_categories',
    'catalog_products_base',
    'catalog_featured_products',
]


@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Product)
def clear_catalog_cache(sender, **kwargs):
    try:
        cache.delete_many(CATALOG_CACHE_KEYS)
    except Exception:
        pass