from django.db import models
from django.utils.text import slugify

# Create your models here.
# ============================================
# PRODUCT MODULE MODELS
# ============================================

class ProductCategory(models.Model):
    """Product Category Model"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    image = models.ImageField(
        upload_to='products/categories/', 
        blank=True, 
        null=True
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Product Model with comprehensive fields for frontend"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(
        ProductCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='products'
    )
    sku = models.CharField(
        max_length=50, 
        unique=True,
        help_text='Stock Keeping Unit'
    )
    featured_image = models.ImageField(upload_to='products/featured/')
    short_description = models.TextField(
        max_length=500,
        help_text='Brief description for listing cards'
    )
    description = models.TextField(help_text='Full product description')
    
    # Pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='Regular price'
    )
    discount_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text='Discounted price (leave empty if no discount)'
    )
    
    # Product Details
    ingredients = models.TextField(
        blank=True, 
        null=True,
        help_text='Product ingredients or composition'
    )
    usage_instructions = models.TextField(
        blank=True, 
        null=True,
        help_text='How to use the product'
    )
    dosage = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text='Recommended dosage'
    )
    warnings = models.TextField(
        blank=True, 
        null=True,
        help_text='Safety warnings and precautions'
    )
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    
    # SEO Fields
    meta_title = models.CharField(
        max_length=60, 
        blank=True, 
        null=True
    )
    meta_description = models.CharField(
        max_length=160, 
        blank=True, 
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        """Return discount price if available, otherwise regular price"""
        return self.discount_price if self.discount_price else self.price

    @property
    def has_discount(self):
        return self.discount_price is not None and self.discount_price < self.price


class ProductImage(models.Model):
    """Additional Product Images (Gallery)"""
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

