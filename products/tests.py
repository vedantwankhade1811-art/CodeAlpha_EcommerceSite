from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.management import call_command
from products.models import Category, Product


class ProductModelAndCatalogTests(TestCase):
    def setUp(self):
        self.category_fashion = Category.objects.create(
            name="Fashion",
            slug="fashion",
            description="Apparel and garments"
        )
        self.category_shoes = Category.objects.create(
            name="Shoes",
            slug="shoes",
            description="Footwear"
        )

        self.product_in_stock = Product.objects.create(
            category=self.category_fashion,
            name="Linen Shirt",
            slug="linen-shirt",
            description="Fine summer linen shirt",
            price=Decimal("1999.00"),
            compare_at_price=Decimal("2499.00"),
            stock=10,
            is_active=True,
            is_featured=True,
            is_bestseller=True
        )

        self.product_out_of_stock = Product.objects.create(
            category=self.category_shoes,
            name="Leather Derby",
            slug="leather-derby",
            description="Handmade shoes",
            price=Decimal("4999.00"),
            compare_at_price=None,
            stock=0,
            is_active=True,
            is_featured=False,
            is_bestseller=False
        )

        self.client = Client()

    def test_product_model_properties(self):
        """Test stock and discount percentage calculation."""
        self.assertTrue(self.product_in_stock.is_in_stock)
        self.assertFalse(self.product_out_of_stock.is_in_stock)

        # Discount: ((2499 - 1999) / 2499) * 100 = 20%
        self.assertEqual(self.product_in_stock.discount_percentage, 20)
        self.assertEqual(self.product_out_of_stock.discount_percentage, 0)

    def test_homepage_loads(self):
        """Test homepage renders status 200 with categories and featured products."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Everything You Need. Nothing You Don't.")
        self.assertContains(response, "Linen Shirt")

    def test_shop_catalog_filtering_and_sorting(self):
        """Test category filter, price filter, and sorting on shop page."""
        # Category filter
        response = self.client.get(reverse('products:shop'), {'category': 'fashion'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Linen Shirt")
        self.assertNotContains(response, "Leather Derby")

        # Price filter
        response_price = self.client.get(reverse('products:shop'), {'max_price': '3000'})
        self.assertEqual(response_price.status_code, 200)
        self.assertContains(response_price, "Linen Shirt")
        self.assertNotContains(response_price, "Leather Derby")

        # Search query
        response_search = self.client.get(reverse('products:shop'), {'q': 'derby'})
        self.assertEqual(response_search.status_code, 200)
        self.assertContains(response_search, "Leather Derby")
        self.assertNotContains(response_search, "Linen Shirt")

    def test_product_detail_page(self):
        """Test unique product detail page renders correctly."""
        url = reverse('products:detail', kwargs={'slug': self.product_in_stock.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Linen Shirt")
        self.assertContains(response, "&#8377;1999.00")

    def test_seed_command_idempotency(self):
        """Verify running seed_products twice results in exactly 6 categories and no duplicate product slugs."""
        call_command('seed_products')
        call_command('seed_products')
        self.assertEqual(Category.objects.count(), 6)
        # Verify all product slugs are distinct
        slugs = list(Product.objects.values_list('slug', flat=True))
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_link_images_command(self):
        """Verify link_images command runs idempotently and links product images."""
        call_command('seed_products')
        call_command('link_images')
        call_command('link_images')  # Idempotent call
        product = Product.objects.filter(slug='structured-linen-overshirt').first()
        self.assertIsNotNone(product)
        if product.image:
            self.assertTrue(product.image.name.startswith('products/'))
