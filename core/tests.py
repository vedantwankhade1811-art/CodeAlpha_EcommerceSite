from django.test import TestCase, Client
from django.urls import reverse


class CoreStaticAndPolicyPagesTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_renders(self):
        """Verify homepage renders 200 OK."""
        res = self.client.get(reverse('core:home'))
        self.assertEqual(res.status_code, 200)

    def test_about_page_renders(self):
        """Verify About Cartza page renders 200 OK with correct template."""
        res = self.client.get(reverse('core:about'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'core/about.html')
        self.assertContains(res, "Everything You Need.")
        self.assertContains(res, "Our Three Tenets")

    def test_shipping_page_renders(self):
        """Verify Shipping & Delivery page renders 200 OK with rates table."""
        res = self.client.get(reverse('core:shipping'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'core/shipping.html')
        self.assertContains(res, "Shipping &amp; Delivery Policy")
        self.assertContains(res, "Orders &#8377;999 and above")
        self.assertContains(res, "&#8377;79.00")

    def test_returns_page_renders(self):
        """Verify Returns & Exchange page renders 200 OK with 3-step process."""
        res = self.client.get(reverse('core:returns'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'core/returns.html')
        self.assertContains(res, "Returns &amp; Exchange Policy")
        self.assertContains(res, "7-DAY RESTFUL GUARANTEE")

    def test_privacy_page_renders(self):
        """Verify Privacy Policy page renders 200 OK."""
        res = self.client.get(reverse('core:privacy'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'core/privacy.html')
        self.assertContains(res, "Privacy Policy")
        self.assertContains(res, "Zero-Sale Policy")

    def test_terms_page_renders(self):
        """Verify Terms & Conditions page renders 200 OK."""
        res = self.client.get(reverse('core:terms'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'core/terms.html')
        self.assertContains(res, "Terms &amp; Conditions")
        self.assertContains(res, "Governing Law")
