from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirmation/<str:order_number>/', views.order_confirmation_view, name='confirmation'),
    path('history/', views.order_list_view, name='history'),
    path('payment/verify/', views.payment_verify_view, name='payment_verify'),
    path('payment/failed/', views.payment_failed_view, name='payment_failed'),
    path('payment/webhook/', views.payment_webhook_view, name='payment_webhook'),
    path('payment/retry/<str:order_number>/', views.payment_retry_view, name='payment_retry'),
    path('payment/<str:order_number>/', views.payment_process_view, name='payment_process'),
    path('<str:order_number>/', views.order_detail_view, name='detail'),
]
