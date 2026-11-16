from django.core.mail import send_mail
from django.shortcuts import redirect, render
from cart.cart import Cart
from .models import Order, OrderItem


def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('catalog:product_list')

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            city=request.POST.get('city'),
            address=request.POST.get('address'),
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
            subject=f'TechZone: Замовлення #{order.id} прийнято!',
            message=f'Дякуємо, {order.first_name}! Ваше замовлення #{order.id} на суму {order.get_total_cost()} ₴ прийнято в обробку.',
            from_email='noreply@techzone.ua',
            recipient_list=[order.email],
            fail_silently=True,
        )

        return render(request, 'orders/created.html', {'order': order})

    return render(request, 'orders/create.html', {'cart': cart})