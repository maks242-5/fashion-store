from datetime import timedelta
from decimal import Decimal
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Category, Product
from .forms import CheckoutForm, CouponApplyForm
from .models import Coupon, Order, OrderItem, OrderStatusHistory, ShippingAddress


class OrderModelsTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title='Laptops', slug='laptops')
        self.product = Product.objects.create(
            category=self.category,
            title='Test Laptop',
            slug='test-laptop',
            price=Decimal('1000.00'),
            stock_quantity=10,
            is_active=True,
        )
        self.address = ShippingAddress.objects.create(
            full_name='Ivan Petrenko',
            city='Kyiv',
            address='NP #1',
            postal_code='01001',
            phone='+380501234567',
        )
        self.order = Order.objects.create(
            shipping_address=self.address,
            status='new',
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=Decimal('1000.00'),
            quantity=3,
        )

    def test_order_creation_creates_status_history(self):
        self.assertTrue(
            OrderStatusHistory.objects.filter(order=self.order, status='new').exists()
        )

    def test_cancelling_order_restores_stock_once(self):
        self.order.status = 'cancelled'
        self.order.save()

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 13)
        self.assertTrue(
            OrderStatusHistory.objects.filter(order=self.order, status='cancelled').exists()
        )

        self.order.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 13)


class OrderFormsTest(TestCase):
    def test_checkout_form_valid(self):
        form = CheckoutForm(data={
            'full_name': 'Olena Koval',
            'address': 'NP #5',
            'city': 'Lviv',
            'postal_code': '79000',
            'phone': '+380671112233',
        })
        self.assertTrue(form.is_valid())

    def test_checkout_form_invalid_missing_full_name(self):
        form = CheckoutForm(data={
            'full_name': '',
            'address': 'NP #5',
            'city': 'Lviv',
            'postal_code': '79000',
            'phone': '+380671112233',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)

    def test_coupon_apply_form(self):
        form = CouponApplyForm(data={'code': 'TECH10'})
        self.assertTrue(form.is_valid())


class OrderViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(title='Phones', slug='phones')
        self.product = Product.objects.create(
            category=self.category,
            title='Phone X',
            slug='phone-x',
            price=Decimal('500.00'),
            stock_quantity=5,
            is_active=True,
        )
        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code='SALE20',
            discount=20,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=7),
            max_uses=10,
            used_count=0,
            active=True,
        )

    def test_apply_valid_coupon(self):
        response = self.client.post(reverse('orders:apply_coupon'), {'code': 'sale20'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get('coupon_id'), self.coupon.id)

    def test_checkout_decrements_stock_and_increments_coupon(self):
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {'quantity': 2, 'price': str(self.product.price)}
        }
        session['coupon_id'] = self.coupon.id
        session.save()

        response = self.client.post(reverse('orders:checkout'), {
            'full_name': 'Maks Bondar',
            'address': 'NP #12',
            'city': 'Odesa',
            'postal_code': '65000',
            'phone': '+380931234567',
        })

        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.coupon.refresh_from_db()

        self.assertEqual(self.product.stock_quantity, 3)
        self.assertEqual(self.coupon.used_count, 1)
        self.assertEqual(Order.objects.count(), 1)