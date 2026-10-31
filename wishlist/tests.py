from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from wishlist.models import WishlistItem


class WishlistTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='diya',
            email='diya@example.com',
            password='Password123!'
        )
        self.category = Category.objects.create(name="Accessories", slug="accessories")
        self.product = Product.objects.create(
            category=self.category,
            name="Silk Scarf",
            slug="silk-scarf",
            description="Pure mulberry silk",
            price=Decimal("1299.00"),
            stock=15,
            is_active=True
        )

    def test_empty_wishlist_renders(self):
        """Verify empty wishlist page displays empty state."""
        res = self.client.get(reverse('wishlist:detail'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Your Wishlist is Empty")
        self.assertTemplateUsed(res, 'wishlist/wishlist.html')

    def test_toggle_wishlist_authenticated(self):
        """Logged in user can toggle product in and out of wishlist."""
        self.client.login(username='diya', password='Password123!')

        # 1. Add to wishlist
        res = self.client.post(reverse('wishlist:toggle', kwargs={'product_id': self.product.id}))
        self.assertTrue(WishlistItem.objects.filter(user=self.user, product=self.product).exists())

        # Check detail page
        detail_res = self.client.get(reverse('wishlist:detail'))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, "Silk Scarf")

        # 2. Toggle off
        res_off = self.client.post(reverse('wishlist:toggle', kwargs={'product_id': self.product.id}))
        self.assertFalse(WishlistItem.objects.filter(user=self.user, product=self.product).exists())

    def test_toggle_wishlist_ajax(self):
        """AJAX request returns JSON with is_wishlisted and wishlist_count."""
        self.client.login(username='diya', password='Password123!')
        res = self.client.post(
            reverse('wishlist:toggle', kwargs={'product_id': self.product.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['is_wishlisted'])
        self.assertEqual(data['wishlist_count'], 1)

    def test_toggle_wishlist_guest_session(self):
        """Unauthenticated guest saves wishlist to session."""
        res = self.client.post(
            reverse('wishlist:toggle', kwargs={'product_id': self.product.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['is_wishlisted'])
        self.assertEqual(data['wishlist_count'], 1)

        # Verify detail page displays item for guest
        detail_res = self.client.get(reverse('wishlist:detail'))
        self.assertContains(detail_res, "Silk Scarf")

    def test_remove_wishlist_item(self):
        """Explicit removal removes product from user wishlist."""
        self.client.login(username='diya', password='Password123!')
        WishlistItem.objects.create(user=self.user, product=self.product)

        res = self.client.post(reverse('wishlist:remove', kwargs={'product_id': self.product.id}))
        self.assertRedirects(res, reverse('wishlist:detail'))
        self.assertFalse(WishlistItem.objects.filter(user=self.user, product=self.product).exists())
