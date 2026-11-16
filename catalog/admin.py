from django.contrib import admin
from .models import Category, Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'id')
    
    list_filter = ('category',)
    
    list_editable = ('price',)
    
    search_fields = ('title', 'description')
    
    prepopulated_fields = {'slug': ('title',)}
    
    inlines = [ProductImageInline]