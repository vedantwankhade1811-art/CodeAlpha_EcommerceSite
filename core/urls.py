from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_view, name='about'),
    path('shipping/', views.shipping_view, name='shipping'),
    path('returns/', views.returns_view, name='returns'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('newsletter/subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
]
