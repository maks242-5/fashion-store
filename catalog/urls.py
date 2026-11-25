from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('suggestions/', views.search_suggestions, name='search_suggestions'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
]