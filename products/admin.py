from django.contrib import admin
from products.models import (
    ProductCategory, Product, ProductImage,
    
)
# Register your models here.

# ============================================
# PRODUCT MODULE ADMIN
# ============================================

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'discount_price', 'is_active', 'is_featured', 'in_stock']
    list_filter = ['is_active', 'is_featured', 'in_stock', 'category']
    search_fields = ['name', 'sku', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    ordering = ['-created_at']
