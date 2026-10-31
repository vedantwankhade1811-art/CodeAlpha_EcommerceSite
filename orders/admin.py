from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_slug', 'price', 'quantity', 'size', 'color', 'line_total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email', 'status', 'is_paid', 'grand_total', 'payment_method', 'created_at']
    list_filter = ['status', 'is_paid', 'payment_method', 'created_at']
    search_fields = ['order_number', 'full_name', 'email', 'phone', 'city', 'pincode']
    readonly_fields = ['order_number', 'subtotal', 'shipping_fee', 'grand_total', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
