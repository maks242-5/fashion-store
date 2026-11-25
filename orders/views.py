from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from cart.cart import Cart
from orders.forms import CheckoutForm, CouponApplyForm
from .models import Coupon, Order, OrderItem


def _invalidate_catalog_cache():
    try:
        cache.delete('catalog_products_base')
        cache.delete('catalog_featured_products')
    except Exception:
        pass


def apply_coupon(request):
    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip()
        if not code:
            messages.warning(request, 'Введіть промокод.')
            return redirect('orders:checkout')

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, 'Такого промокоду не існує.')
            return redirect('orders:checkout')

        if coupon.is_valid():
            request.session['coupon_id'] = coupon.id
            messages.success(request, f'Промокод {coupon.code} застосовано (-{coupon.discount}%).')
        else:
            request.session['coupon_id'] = None
            messages.error(request, 'Термін дії промокоду закінчився або вичерпано ліміт використань.')

    return redirect('orders:checkout')


@transaction.atomic
def checkout_view(request):
    cart = Cart(request)
    coupon_form = CouponApplyForm()

    coupon_id = request.session.get('coupon_id')
    applied_coupon = None
    discount = 0
    subtotal = cart.get_total_price()

    if coupon_id:
        try:
            applied_coupon = Coupon.objects.get(id=coupon_id)
            if applied_coupon.is_valid():
                discount = (subtotal * applied_coupon.discount) / 100
            else:
                request.session['coupon_id'] = None
                applied_coupon = None
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None

    final_total = subtotal - discount

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if len(cart) == 0:
            messages.warning(request, 'Ваш кошик порожній.')
            return redirect('orders:checkout')

        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = (
                request.user if request.user.is_authenticated else None
            )
            shipping_address.save()

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                shipping_address=shipping_address,
                coupon=applied_coupon,
                discount_amount=discount,
                status='new',
            )

            for item in cart:
                product = item['product']
                quantity = item['quantity']

                if product.stock_quantity < quantity:
                    transaction.set_rollback(True)
                    form.add_error(
                        None,
                        f'Вибачте, товару "{product.title}" залишилось лише {product.stock_quantity} шт.',
                    )
                    return render(request, 'orders/create.html', {
                        'form': form,
                        'coupon_form': coupon_form,
                        'cart': cart,
                        'applied_coupon': applied_coupon,
                        'discount': discount,
                        'final_total': final_total,
                    })

                product.stock_quantity = F('stock_quantity') - quantity
                product.save(update_fields=['stock_quantity'])
                product.refresh_from_db(fields=['stock_quantity'])

                if product.stock_quantity <= 0:
                    product.stock_quantity = 0
                    product.save(update_fields=['stock_quantity'])

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,
                    quantity=quantity,
                )

            if applied_coupon:
                applied_coupon.used_count = F('used_count') + 1
                applied_coupon.save(update_fields=['used_count'])
                applied_coupon.refresh_from_db(fields=['used_count'])
                if 'coupon_id' in request.session:
                    del request.session['coupon_id']

            _invalidate_catalog_cache()
            cart.clear()

            recipient_email = getattr(order, 'email', None) or form.cleaned_data.get('email')
            if recipient_email:
                html_content = render_to_string('orders/order_email.html', {'order': order})
                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(
                    subject=f'Підтвердження замовлення #{order.id}',
                    body=text_content,
                    from_email=None,
                    to=[recipient_email],
                )
                email.attach_alternative(html_content, 'text/html')
                email.send(fail_silently=True)

            return render(request, 'orders/created.html', {'order': order})

    else:
        form = CheckoutForm()

    return render(request, 'orders/create.html', {
        'form': form,
        'coupon_form': coupon_form,
        'cart': cart,
        'applied_coupon': applied_coupon,
        'discount': discount,
        'final_total': final_total,
    })