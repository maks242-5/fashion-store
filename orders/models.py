from django.conf import settings
from django.db import models
from catalog.models import Product


class Order(models.Model):
    STATUS_CHOICES = (
        ('new', '🆕 Нове'),
        ('processing', '🔄 В обробці'),
        ('shipped', '🚚 Відправлено'),
        ('completed', '✅ Виконано'),
        ('cancelled', '❌ Скасовано'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
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

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.price * self.quantity