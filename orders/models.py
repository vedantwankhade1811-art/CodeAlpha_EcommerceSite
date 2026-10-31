from decimal import Decimal
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from products.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('payment_failed', 'Payment Failed'),
    ]

    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery (Pay at Doorstep)'),
        ('upi', 'UPI / Instant QR Code'),
        ('card', 'Credit / Debit Card'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid & Verified'),
        ('pending_cod', 'Pay on Delivery (COD)'),
        ('failed', 'Payment Failed'),
        ('cancelled', 'Payment Cancelled'),
        ('refunded', 'Refunded'),
    ]

    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    # Shipping Details
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    # Financial Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment & Gateway Processing
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    notes = models.TextField(blank=True)

    # Gateway Tracking Fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    payment_error_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} ({self.full_name})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"CRZ-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('orders:detail', kwargs={'order_number': self.order_number})

    @property
    def is_online_payment(self):
        return self.payment_method in ['upi', 'card']

    @property
    def can_retry_payment(self):
        return self.is_online_payment and not self.is_paid and self.status in ['pending_payment', 'payment_failed']

    @property
    def amount_in_paise(self):
        return int(round(self.grand_total * Decimal('100.00')))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=255)
    product_slug = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} ({self.order.order_number})"
