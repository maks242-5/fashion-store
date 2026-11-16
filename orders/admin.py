from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'phone', 'city', 'paid', 'created_at')  # Виправлено тут
    list_filter = ('paid', 'created_at', 'city')  # І тут
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'city', 'address')
    list_editable = ('paid',)
    inlines = [OrderItemInline]