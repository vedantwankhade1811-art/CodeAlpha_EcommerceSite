from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='detail'),
    path('add/<int:product_id>/', views.add_to_cart_view, name='add'),
    path('update/<path:item_key>/', views.update_cart_view, name='update'),
    path('remove/<path:item_key>/', views.remove_from_cart_view, name='remove'),
    path('clear/', views.clear_cart_view, name='clear'),
    path('apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon_view, name='remove_coupon'),
]
