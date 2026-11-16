from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from catalog.models import Product
from orders.models import Order, OrderItem
from .cart import Cart


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)
    return redirect('cart:cart_detail')


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)

    # Обробка оформлення замовлення і миттєвої оплати прямо з кошика
    if request.method == 'POST':
        if len(cart) == 0:
            return redirect('cart:cart_detail')

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            city=request.POST.get('city'),
            address=request.POST.get('address'),
            paid=True,  # Імітуємо успішну онлайн-оплату
        )
        
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity'],
            )
            product = item['product']
            if product.stock_quantity >= item['quantity']:
                product.stock_quantity -= item['quantity']
                product.save()

        cart.clear()

        send_mail(
            subject=f'TechZone: Замовлення #{order.id} успішно оплачено!',
            message=f'Дякуємо, {order.first_name}! Ваше замовлення #{order.id} на суму {order.get_total_cost()} ₴ оплачено та прийнято в обробку.',
            from_email='noreply@techzone.ua',
            recipient_list=[order.email],
            fail_silently=True,
        )

        return render(request, 'orders/created.html', {'order': order})

    return render(request, 'cart/detail.html', {'cart': cart})