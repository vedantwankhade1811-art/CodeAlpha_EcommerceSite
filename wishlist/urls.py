from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist_detail_view, name='detail'),
    path('toggle/<int:product_id>/', views.toggle_wishlist_view, name='toggle'),
    path('remove/<int:product_id>/', views.remove_from_wishlist_view, name='remove'),
]
