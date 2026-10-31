from django.contrib import admin
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active', 'image_preview')
    list_filter = ('category', 'is_active', 'is_featured', 'is_bestseller')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fields = (
        'name', 'slug', 'category', 'description', 
        'price', 'compare_at_price', 'stock', 'image', 
        'is_active', 'is_featured', 'is_bestseller', 
        'available_sizes', 'available_colors', 'specifications'
    )
    inlines = [ProductImageInline]

    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 40px; height: 50px; object-fit: cover; border-radius: 2px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'created_at')
    list_filter = ('is_primary',)
