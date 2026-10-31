from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from products.models import Category, Product


class CartViewsAndCalculationsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Apparel", slug="apparel")
        self.product = Product.objects.create(
            category=self.category,
            name="Classic Linen Shirt",
            slug="classic-linen-shirt",
            description="Pure linen essential",
            price=Decimal("1200.00"),
            stock=5,
            is_active=True
        )
        self.cheap_product = Product.objects.create(
            category=self.category,
            name="Organic Socks",
            slug="organic-socks",
            description="Cotton socks",
            price=Decimal("499.00"),
            stock=10,
            is_active=True
        )

    def test_empty_cart_renders(self):
        """Verify empty shopping bag renders clean empty state."""
        res = self.client.get(reverse('cart:detail'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Your Shopping Bag is Empty")
        self.assertEqual(res.context['cart_items'], [])
        self.assertEqual(res.context['subtotal'], Decimal('0.00'))

    def test_add_to_cart_standard_post(self):
        """Verify standard form submit adds item and redirects to cart detail."""
        res = self.client.post(reverse('cart:add', kwargs={'product_id': self.product.id}), {
            'quantity': 2,
            'selected_size': 'M',
            'selected_color': 'White',
            'buy_now': '0',
        })
        self.assertRedirects(res, reverse('cart:detail'))

        # Check cart page now has 2 units and subtotal 2400.00
        detail_res = self.client.get(reverse('cart:detail'))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, "Classic Linen Shirt")
        self.assertEqual(detail_res.context['total_items'], 2)
        self.assertEqual(detail_res.context['subtotal'], Decimal('2400.00'))
        # Over ₹999 threshold -> Free shipping
        self.assertEqual(detail_res.context['shipping'], Decimal('0.00'))
        self.assertEqual(detail_res.context['grand_total'], Decimal('2400.00'))

    def test_add_to_cart_ajax(self):
        """Verify AJAX POST returns JSON with success status and cart_count."""
        res = self.client.post(
            reverse('cart:add', kwargs={'product_id': self.product.id}),
            {
                'quantity': 1,
                'selected_size': 'L',
                'selected_color': 'Navy',
                'buy_now': '0',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['cart_count'], 1)
        self.assertIn("Classic Linen Shirt", data['message'])

    def test_add_to_cart_buy_now(self):
        """Verify buy_now flag redirects directly to cart detail."""
        res = self.client.post(reverse('cart:add', kwargs={'product_id': self.product.id}), {
            'quantity': 1,
            'selected_size': 'M',
            'selected_color': 'Navy',
            'buy_now': '1',
        })
        self.assertRedirects(res, reverse('cart:detail'))

    def test_stock_capping(self):
        """Verify adding more than available stock is capped at product.stock."""
        # Stock is 5; request 10
        self.client.post(reverse('cart:add', kwargs={'product_id': self.product.id}), {
            'quantity': 10,
            'buy_now': '0',
        })
        detail_res = self.client.get(reverse('cart:detail'))
        self.assertEqual(detail_res.context['total_items'], 5)

    def test_shipping_fee_under_threshold(self):
        """Verify shipping fee of ₹79 applies when order subtotal is under ₹999."""
        self.client.post(reverse('cart:add', kwargs={'product_id': self.cheap_product.id}), {
            'quantity': 1,
            'buy_now': '0',
        })
        detail_res = self.client.get(reverse('cart:detail'))
        self.assertEqual(detail_res.context['subtotal'], Decimal('499.00'))
        self.assertEqual(detail_res.context['shipping'], Decimal('79.00'))
        self.assertEqual(detail_res.context['grand_total'], Decimal('578.00'))
        self.assertEqual(detail_res.context['needed_for_free_shipping'], Decimal('500.00'))

    def test_update_quantity_increase_and_decrease(self):
        """Verify increasing and decreasing quantity via update view."""
        self.client.post(reverse('cart:add', kwargs={'product_id': self.cheap_product.id}), {
            'quantity': 2,
            'selected_size': 'M',
            'selected_color': 'Beige',
        })
        item_key = f"{self.cheap_product.id}_M_Beige"

        # Increase by 1
        self.client.post(reverse('cart:update', kwargs={'item_key': item_key}), {'action': 'increase'})
        res = self.client.get(reverse('cart:detail'))
        self.assertEqual(res.context['total_items'], 3)

        # Decrease by 1
        self.client.post(reverse('cart:update', kwargs={'item_key': item_key}), {'action': 'decrease'})
        res = self.client.get(reverse('cart:detail'))
        self.assertEqual(res.context['total_items'], 2)

    def test_remove_and_clear_cart(self):
        """Verify item removal and full cart clearing."""
        self.client.post(reverse('cart:add', kwargs={'product_id': self.cheap_product.id}), {
            'quantity': 2,
        })
        item_key = str(self.cheap_product.id)

        # Remove single item
        self.client.post(reverse('cart:remove', kwargs={'item_key': item_key}))
        res = self.client.get(reverse('cart:detail'))
        self.assertEqual(res.context['total_items'], 0)

        # Add again then clear
        self.client.post(reverse('cart:add', kwargs={'product_id': self.cheap_product.id}), {
            'quantity': 1,
        })
        self.client.post(reverse('cart:clear'))
        res_cleared = self.client.get(reverse('cart:detail'))
        self.assertEqual(res_cleared.context['total_items'], 0)

    def test_apply_valid_coupon_cartza15(self):
        """Verify applying CARTZA15 gives 15% discount."""
        self.client.post(reverse('cart:add', kwargs={'product_id': self.product.id}), {
            'quantity': 1,  # ₹1200
        })
        # Apply coupon
        res = self.client.post(reverse('cart:apply_coupon'), {'coupon_code': 'CARTZA15'})
        self.assertRedirects(res, reverse('cart:detail'))

        detail_res = self.client.get(reverse('cart:detail'))
        self.assertEqual(detail_res.context['discount'], Decimal('180.00'))  # 15% of 1200
        self.assertEqual(detail_res.context['grand_total'], Decimal('1020.00'))

    def test_apply_coupon_cartza_with_free_shipping(self):
        """Verify applying CARTZA grants 10% discount plus free express delivery."""
        self.client.post(reverse('cart:add', kwargs={'product_id': self.cheap_product.id}), {
            'quantity': 1,  # ₹499
        })
        self.client.post(reverse('cart:apply_coupon'), {'coupon_code': 'CARTZA'})
        detail_res = self.client.get(reverse('cart:detail'))
        # 10% of 499 = 49.90; shipping is ₹0 instead of ₹79
        self.assertEqual(detail_res.context['discount'], Decimal('49.90'))
        self.assertEqual(detail_res.context['shipping'], Decimal('0.00'))
        self.assertEqual(detail_res.context['grand_total'], Decimal('449.10'))

    def test_remove_coupon(self):
        """Verify removing applied coupon restores standard totals."""
        self.client.post(reverse('cart:add', kwargs={'product_id': self.product.id}), {'quantity': 1})
        self.client.post(reverse('cart:apply_coupon'), {'coupon_code': 'CARTZA15'})
        self.client.post(reverse('cart:remove_coupon'))

        detail_res = self.client.get(reverse('cart:detail'))
        self.assertEqual(detail_res.context['discount'], Decimal('0.00'))
        self.assertIsNone(detail_res.context['coupon_code'])

