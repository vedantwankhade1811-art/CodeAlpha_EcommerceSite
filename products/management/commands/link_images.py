import os
import glob
from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Product, ProductImage, Category


class Command(BaseCommand):
    help = 'Assigns saved media images to products and categories idempotently'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Linking saved images to products and categories..."))

        products_linked = 0
        gallery_linked = 0
        categories_linked = 0

        # 1. Link Products
        for product in Product.objects.all():
            main_rel_path = f"products/{product.slug}.jpg"
            main_abs_path = os.path.join(settings.MEDIA_ROOT, main_rel_path)

            if os.path.exists(main_abs_path):
                # Update main image on Product model
                if product.image != main_rel_path:
                    product.image = main_rel_path
                    product.save(update_fields=['image'])
                products_linked += 1

                # Ensure primary ProductImage exists
                primary_img = ProductImage.objects.filter(product=product, is_primary=True).first()
                if primary_img:
                    if primary_img.image != main_rel_path:
                        primary_img.image = main_rel_path
                        primary_img.alt_text = product.name
                        primary_img.save(update_fields=['image', 'alt_text'])
                else:
                    ProductImage.objects.create(
                        product=product,
                        image=main_rel_path,
                        alt_text=product.name,
                        is_primary=True
                    )

            # Check for gallery / extra detail images
            pattern = os.path.join(settings.MEDIA_ROOT, "products", f"{product.slug}-*.jpg")
            detail_files = glob.glob(pattern)

            for detail_file in detail_files:
                basename = os.path.basename(detail_file)
                detail_rel_path = f"products/{basename}"

                # Avoid duplicates
                existing_gallery = ProductImage.objects.filter(
                    product=product,
                    image=detail_rel_path
                ).first()

                if not existing_gallery:
                    ProductImage.objects.create(
                        product=product,
                        image=detail_rel_path,
                        alt_text=f"{product.name} detail view",
                        is_primary=False
                    )
                    gallery_linked += 1
                else:
                    gallery_linked += 1

        # 2. Link Categories
        for category in Category.objects.all():
            cat_rel_path = f"categories/{category.slug}.jpg"
            cat_abs_path = os.path.join(settings.MEDIA_ROOT, cat_rel_path)

            if os.path.exists(cat_abs_path):
                if category.image != cat_rel_path:
                    category.image = cat_rel_path
                    category.save(update_fields=['image'])
                categories_linked += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully linked images:\n"
            f" - {products_linked} products assigned main image\n"
            f" - {gallery_linked} gallery detail images linked\n"
            f" - {categories_linked} category card images linked"
        ))
