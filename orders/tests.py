from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from orders.models import Order, OrderItem


class CheckoutAndOrdersTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='arjun',
            email='arjun@example.com',
            password='StrongPassword123!',
            first_name='Arjun',
            last_name='Verma'
        )
        self.user.profile.phone = '9876543210'
        self.user.profile.address = '42 Green Glen Layout, Bellandur'
        self.user.profile.city = 'Bengaluru'
        self.user.profile.state = 'Karnataka'
        self.user.profile.pincode = '560103'
        self.user.profile.save()

        self.category = Category.objects.create(name="Shirts", slug="shirts")
        self.product = Product.objects.create(
            category=self.category,
            name="Classic Oxford Shirt",
            slug="classic-oxford-shirt",
            description="Pure cotton shirt",
            price=Decimal("1500.00"),
            stock=10,
            is_active=True
        )

    def test_unauthenticated_checkout_redirects_to_login(self):
        """Unauthenticated user is redirected to login with next parameter."""
        res = self.client.get(reverse('orders:checkout'))
        expected_url = f"{reverse('accounts:login')}?next={reverse('orders:checkout')}"
        self.assertRedirects(res, expected_url)

    def test_empty_cart_checkout_redirects_to_shop(self):
        """Authenticated user with empty cart is redirected to shop."""
        self.client.login(username='arjun', password='StrongPassword123!')
        res = self.client.get(reverse('orders:checkout'))
        self.assertRedirects(res, reverse('products:shop'))

    def test_authenticated_checkout_get_with_cart(self):
        """Authenticated user with cart sees checkout form pre-filled with profile."""
        self.client.login(username='arjun', password='StrongPassword123!')

        # Put item in cart
        self.client.post(reverse('cart:add', kwargs={'product_id': self.product.id}), {
            'quantity': 1,
            'selected_size': 'M',
            'selected_color': 'White',
        })

        res = self.client.get(reverse('orders:checkout'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'orders/checkout.html')
        self.assertContains(res, "Arjun Verma")
        self.assertContains(res, "42 Green Glen Layout")
        self.assertContains(res, "Classic Oxford Shirt")
        self.assertEqual(res.context['subtotal'], Decimal('1500.00'))
        self.assertEqual(res.context['shipping'], Decimal('0.00'))  # Free over ₹999
        self.assertEqual(res.context['grand_total'], Decimal('1500.00'))

    def test_successful_order_placement(self):
        """Placing order creates Order, OrderItems, decrements stock, and clears cart."""
        self.client.login(username='arjun', password='StrongPassword123!')

        # Add 2 items to cart
        self.client.post(reverse('cart:add', kwargs={'product_id': self.product.id}), {
            'quantity': 2,
            'selected_size': 'L',
            'selected_color': 'Blue',
        })

        initial_stock = self.product.stock  # 10

        res = self.client.post(reverse('orders:checkout'), {
            'full_name': 'Arjun Verma',
            'email': 'arjun@example.com',
            'phone': '9876543210',
            'address': '42 Green Glen Layout',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560103',
            'payment_method': 'cod',
            'notes': 'Call on arrival',
        })

        # Must redirect to confirmation
        self.assertEqual(res.status_code, 302)
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.subtotal, Decimal('3000.00'))
        self.assertEqual(order.grand_total, Decimal('3000.00'))
        self.assertFalse(order.is_paid)

        # Order items created
        items = order.items.all()
        self.assertEqual(items.count(), 1)
        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(items[0].size, 'L')

        # Product stock decremented from 10 to 8
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)

        # Cart cleared
        cart_res = self.client.get(reverse('cart:detail'))
        self.assertEqual(cart_res.context['total_items'], 0)

        # Confirmation page renders
        conf_res = self.client.get(reverse('orders:confirmation', kwargs={'order_number': order.order_number}))
        self.assertEqual(conf_res.status_code, 200)
        self.assertContains(conf_res, order.order_number)
        self.assertContains(conf_res, "Arjun Verma")

    def test_order_history_and_detail_views(self):
        """User can view past orders in history and drill down to detail."""
        self.client.login(username='arjun', password='StrongPassword123!')

        order = Order.objects.create(
            user=self.user,
            full_name='Arjun Verma',
            email='arjun@example.com',
            phone='9876543210',
            address='Street 1',
            city='Bengaluru',
            state='Karnataka',
            pincode='560103',
            subtotal=Decimal('1500.00'),
            shipping_fee=Decimal('0.00'),
            grand_total=Decimal('1500.00'),
            payment_method='cod'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name='Classic Oxford Shirt',
            price=Decimal('1500.00'),
            quantity=1,
            line_total=Decimal('1500.00')
        )

        # History view
        history_res = self.client.get(reverse('orders:history'))
        self.assertEqual(history_res.status_code, 200)
        self.assertContains(history_res, order.order_number)

        # Detail view
        detail_res = self.client.get(reverse('orders:detail', kwargs={'order_number': order.order_number}))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, order.order_number)
        self.assertContains(detail_res, "Classic Oxford Shirt")

    def test_online_payment_creates_pending_order_and_routes_to_payment_process(self):
        """Selecting UPI or Card creates an unpaid order with pending_payment status."""
        self.client.login(username='arjun', password='StrongPassword123!')

        # Put item in cart
        self.client.post(reverse('cart:add', kwargs={'product_id': self.product.id}), {'quantity': 1})

        res = self.client.post(reverse('orders:checkout'), {
            'full_name': 'Arjun Verma',
            'email': 'arjun@example.com',
            'phone': '9876543210',
            'address': '42 Green Glen Layout',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560103',
            'payment_method': 'upi',
        })

        order = Order.objects.filter(user=self.user, payment_method='upi').first()
        self.assertIsNotNone(order)
        # CRITICAL RULE: Payment must NOT be simulated as paid!
        self.assertFalse(order.is_paid)
        self.assertEqual(order.status, 'pending_payment')
        self.assertEqual(order.payment_status, 'pending')
        # Redirects to payment processing screen
        self.assertRedirects(res, reverse('orders:payment_process', kwargs={'order_number': order.order_number}))

    def test_payment_verification_success_with_valid_signature(self):
        """Valid cryptographic HMAC signature verifies payment, marks paid, and decrements stock."""
        import hmac, hashlib
        from django.conf import settings

        self.client.login(username='arjun', password='StrongPassword123!')

        order = Order.objects.create(
            user=self.user,
            full_name='Arjun Verma',
            email='arjun@example.com',
            phone='9876543210',
            address='Street 1',
            city='Bengaluru',
            state='Karnataka',
            pincode='560103',
            subtotal=Decimal('1500.00'),
            shipping_fee=Decimal('0.00'),
            grand_total=Decimal('1500.00'),
            payment_method='card',
            payment_status='pending',
            status='pending_payment',
            razorpay_order_id='order_test_12345'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name='Classic Oxford Shirt',
            price=Decimal('1500.00'),
            quantity=1,
            line_total=Decimal('1500.00')
        )

        initial_stock = self.product.stock

        # Compute valid HMAC SHA256 signature
        test_key_id = 'rzp_test_9876543210'
        test_secret = 'valid_test_secret_key_12345'
        payment_id = 'pay_test_99999'
        msg = f"{order.razorpay_order_id}|{payment_id}".encode('utf-8')
        valid_signature = hmac.new(test_secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

        # Send verification request
        with self.settings(RAZORPAY_KEY_ID=test_key_id, RAZORPAY_KEY_SECRET=test_secret):
            res = self.client.post(
                reverse('orders:payment_verify'),
                data={
                    'order_number': order.order_number,
                    'razorpay_order_id': order.razorpay_order_id,
                    'razorpay_payment_id': payment_id,
                    'razorpay_signature': valid_signature
                },
                content_type='application/json'
            )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'success')

        # Order must now be verified as paid
        order.refresh_from_db()
        self.assertTrue(order.is_paid)
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(order.payment_status, 'paid')
        self.assertEqual(order.razorpay_payment_id, payment_id)

        # Inventory decremented
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 1)

    def test_payment_verification_rejected_with_invalid_signature(self):
        """Tampered or invalid signature is rejected and marks order as payment_failed."""
        self.client.login(username='arjun', password='StrongPassword123!')

        order = Order.objects.create(
            user=self.user,
            full_name='Arjun Verma',
            email='arjun@example.com',
            phone='9876543210',
            address='Street 1',
            city='Bengaluru',
            state='Karnataka',
            pincode='560103',
            subtotal=Decimal('1500.00'),
            shipping_fee=Decimal('0.00'),
            grand_total=Decimal('1500.00'),
            payment_method='upi',
            payment_status='pending',
            status='pending_payment',
            razorpay_order_id='order_test_fake'
        )
        initial_stock = self.product.stock

        # Fake tampered signature
        with self.settings(RAZORPAY_KEY_SECRET='real_secret_123'):
            res = self.client.post(
                reverse('orders:payment_verify'),
                data={
                    'order_number': order.order_number,
                    'razorpay_order_id': 'order_test_fake',
                    'razorpay_payment_id': 'pay_fake_000',
                    'razorpay_signature': 'invalid_forged_signature_hex'
                },
                content_type='application/json'
            )

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['status'], 'error')

        # Order must NOT be marked paid!
        order.refresh_from_db()
        self.assertFalse(order.is_paid)
        self.assertEqual(order.status, 'payment_failed')
        self.assertEqual(order.payment_status, 'failed')

        # Stock must NOT be decremented
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock)

    def test_payment_failure_callback_and_retry(self):
        """Payment modal dismissal records failure and retry resets order safely."""
        self.client.login(username='arjun', password='StrongPassword123!')

        order = Order.objects.create(
            user=self.user,
            full_name='Arjun Verma',
            email='arjun@example.com',
            phone='9876543210',
            address='Street 1',
            city='Bengaluru',
            state='Karnataka',
            pincode='560103',
            subtotal=Decimal('1500.00'),
            shipping_fee=Decimal('0.00'),
            grand_total=Decimal('1500.00'),
            payment_method='upi',
            payment_status='pending',
            status='pending_payment'
        )

        # Notify failure / user dismissal
        fail_res = self.client.post(
            reverse('orders:payment_failed'),
            data={'order_number': order.order_number, 'description': 'Customer dismissed modal'},
            content_type='application/json'
        )
        self.assertEqual(fail_res.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(order.status, 'payment_failed')
        self.assertEqual(order.payment_status, 'failed')

        # Customer retries payment
        retry_res = self.client.get(reverse('orders:payment_retry', kwargs={'order_number': order.order_number}))
        self.assertRedirects(retry_res, reverse('orders:payment_process', kwargs={'order_number': order.order_number}))

        order.refresh_from_db()
        self.assertEqual(order.status, 'pending_payment')
        self.assertEqual(order.payment_status, 'pending')

    def test_razorpay_service_is_configured_validation(self):
        """is_configured validates presence of real keys and rejects placeholders."""
        from orders.services import RazorpayService

        with self.settings(RAZORPAY_KEY_ID='', RAZORPAY_KEY_SECRET=''):
            self.assertFalse(RazorpayService.is_configured())

        with self.settings(RAZORPAY_KEY_ID='rzp_test_YourKeyIdHere', RAZORPAY_KEY_SECRET='YourKeySecretHere'):
            self.assertFalse(RazorpayService.is_configured())

        with self.settings(RAZORPAY_KEY_ID='rzp_test_valid12345', RAZORPAY_KEY_SECRET='real_test_secret_67890'):
            self.assertTrue(RazorpayService.is_configured())

    def test_razorpay_service_signature_verification_sdk(self):
        """RazorpayService uses official SDK verification for valid and invalid signatures."""
        from orders.services import RazorpayService
        import hmac, hashlib

        order_id = 'order_test_98765'
        payment_id = 'pay_test_54321'
        secret = 'test_signature_secret_key'

        msg = f"{order_id}|{payment_id}".encode('utf-8')
        valid_sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

        with self.settings(RAZORPAY_KEY_ID='rzp_test_sample', RAZORPAY_KEY_SECRET=secret):
            # Valid signature must verify successfully
            self.assertTrue(RazorpayService.verify_signature(order_id, payment_id, valid_sig))

            # Tampered signature must fail verification
            self.assertFalse(RazorpayService.verify_signature(order_id, payment_id, 'tampered_invalid_signature'))

            # Missing arguments must fail verification
            self.assertFalse(RazorpayService.verify_signature('', payment_id, valid_sig))
            self.assertFalse(RazorpayService.verify_signature(order_id, '', valid_sig))
            self.assertFalse(RazorpayService.verify_signature(order_id, payment_id, ''))

    def test_payment_process_view_unconfigured_shows_setup_notice(self):
        """When Razorpay keys are not configured, payment page renders the setup notice."""
        self.client.login(username='arjun', password='StrongPassword123!')

        order = Order.objects.create(
            user=self.user,
            full_name='Arjun Verma',
            email='arjun@example.com',
            phone='9876543210',
            address='Street 1',
            city='Bengaluru',
            state='Karnataka',
            pincode='560103',
            subtotal=Decimal('1500.00'),
            shipping_fee=Decimal('0.00'),
            grand_total=Decimal('1500.00'),
            payment_method='upi',
            payment_status='pending',
            status='pending_payment'
        )

        with self.settings(RAZORPAY_KEY_ID='', RAZORPAY_KEY_SECRET=''):
            res = self.client.get(reverse('orders:payment_process', kwargs={'order_number': order.order_number}))
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, "Razorpay Payment Gateway Setup Notice")
            self.assertContains(res, "RAZORPAY_KEY_ID")
            self.assertNotContains(res, 'https://checkout.razorpay.com/v1/checkout.js')

    def test_payment_process_view_configured_renders_razorpay_modal_script(self):
        """When Razorpay keys and order ID exist, payment page renders checkout script and pay button."""
        self.client.login(username='arjun', password='StrongPassword123!')

        order = Order.objects.create(
            user=self.user,
            full_name='Arjun Verma',
            email='arjun@example.com',
            phone='9876543210',
            address='Street 1',
            city='Bengaluru',
            state='Karnataka',
            pincode='560103',
            subtotal=Decimal('1500.00'),
            shipping_fee=Decimal('0.00'),
            grand_total=Decimal('1500.00'),
            payment_method='card',
            payment_status='pending',
            status='pending_payment',
            razorpay_order_id='order_test_ready123'
        )

        with self.settings(RAZORPAY_KEY_ID='rzp_test_valid123', RAZORPAY_KEY_SECRET='real_secret_456'):
            res = self.client.get(reverse('orders:payment_process', kwargs={'order_number': order.order_number}))
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, 'https://checkout.razorpay.com/v1/checkout.js')
            self.assertContains(res, 'id="rzp-button"')
            self.assertNotContains(res, "Razorpay Payment Gateway Setup Notice")

