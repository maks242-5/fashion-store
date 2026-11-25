from django.contrib import admin
from .models import Order, Coupon, OrderItem, OrderStatusHistory, ShippingAddress


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity')

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('status', 'created_at')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'phone', 'city', 'status', 'paid', 'created_at')
    list_filter = ('status', 'paid', 'created_at', 'city')
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'city', 'address')
    list_editable = ('paid', 'status')
    inlines = [OrderItemInline, OrderStatusHistoryInline]

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'city', 'phone')




@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'valid_from', 'valid_to', 'max_uses', 'used_count', 'active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']