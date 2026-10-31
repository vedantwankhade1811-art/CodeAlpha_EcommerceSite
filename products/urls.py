from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('shop/', views.shop_view, name='shop'),
    path('products/', views.shop_view, name='all_products'),
    path('category/<slug:category_slug>/', views.shop_view, name='category_shop'),
    path('products/<slug:slug>/', views.product_detail_view, name='detail'),
    path('<slug:category_slug>/', views.category_direct_view, name='category_direct'),
]
