from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone
from catalog.models import Product


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.active:
            return False
        if not (self.valid_from <= now <= self.valid_to):
            return False
        if self.used_count >= self.max_uses:
            return False
        return True


class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.full_name}, {self.city}'


class Order(models.Model):
    STATUS_CHOICES = (
        ('new', '🆕 Нове'),
        ('processing', '🔄 В обробці'),
        ('shipped', '🚚 Відправлено'),
        ('completed', '✅ Виконано'),
        ('cancelled', '❌ Скасовано'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    first_name = models.CharField('Ім’я', max_length=50)
    last_name = models.CharField('Прізвище', max_length=50)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=20)
    city = models.CharField('Місто', max_length=100)
    address = models.CharField('Адреса / Відділення НП', max_length=250)

    status = models.CharField('Статус замовлення', max_length=20, choices=STATUS_CHOICES, default='new')
    paid = models.BooleanField('Оплачено', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'

    def __str__(self):
        return f'Замовлення #{self.id} ({self.get_status_display()})'

    def get_subtotal(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_total_cost(self):
        subtotal = self.get_subtotal()
        return subtotal - self.discount_amount

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_status = Order.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        super().save(*args, **kwargs)

        if is_new:
            OrderStatusHistory.objects.create(order=self, status=self.status)
        elif old_status != self.status:
            OrderStatusHistory.objects.create(order=self, status=self.status)

            if self.status == 'cancelled' and old_status != 'cancelled':
                for item in self.items.select_related('product'):
                    item.product.stock_quantity = F('stock_quantity') + item.quantity
                    item.product.save(update_fields=['stock_quantity'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.price * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, related_name='status_history', on_delete=models.CASCADE)
    status = models.CharField('Статус', max_length=20, choices=Order.STATUS_CHOICES)
    created_at = models.DateTimeField('Дата зміни', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Історія статусу'
        verbose_name_plural = 'Історія статусів'

    def __str__(self):
        return f'Замовлення #{self.order.id} -> {self.get_status_display()}'