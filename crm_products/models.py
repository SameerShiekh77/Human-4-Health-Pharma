from django.db import models
from django.utils import timezone
from datetime import timedelta


# ============================================================
# CRM PRODUCTS APP — crm_products/models.py
# Handles: Product Master + Batch Management + Company Stock
# ============================================================


class Division(models.Model):
    """
    Sales Division (e.g., Cardiology, Gastro, General)
    Used in both Products and Sales Structure.
    Defined here to avoid circular imports.
    """
    division_id = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=100)
    manager_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Division'
        verbose_name_plural = 'Divisions'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.division_id:
            last = Division.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.division_id = f"DIV-{next_id:04d}"
        super().save(*args, **kwargs)


class ProductMaster(models.Model):
    """
    Master catalogue of all pharmaceutical products manufactured.
    """

    CATEGORY_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    # Auto-generated Product ID
    product_id = models.CharField(max_length=20, unique=True, editable=False)

    # Names
    product_name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200)
    brand_name = models.CharField(max_length=200)

    # Classification
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    division = models.ForeignKey(
        Division,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    # Specs
    strength = models.CharField(
        max_length=100,
        help_text='e.g., 500mg, 250mg/5ml'
    )
    packing_size = models.CharField(
        max_length=100,
        help_text='e.g., 10x10, 1x100ml'
    )

    # Pricing (PKR)
    manufacturing_cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    trade_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text='Price at which trade buys'
    )
    retail_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text='MRP — Maximum Retail Price'
    )
    distributor_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text='Price charged to distributor'
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Optional extra info
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='crm/products/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product_name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.product_name} ({self.strength})"

    def save(self, *args, **kwargs):
        if not self.product_id:
            last = ProductMaster.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.product_id = f"PROD-{next_id:05d}"
        super().save(*args, **kwargs)

    @property
    def profit_margin(self):
        """Gross margin per unit sold at trade price."""
        if self.trade_price and self.manufacturing_cost_per_unit:
            return float(self.trade_price) - float(self.manufacturing_cost_per_unit)
        return 0


class BatchManagement(models.Model):
    """
    Individual production batch for a product.
    Tracks quantities through lifecycle: manufactured → distributed → remaining.
    """

    BATCH_STATUS_CHOICES = [
        ('active', 'Active'),
        ('near_expiry', 'Near Expiry'),
        ('expired', 'Expired'),
    ]

    batch_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='batches'
    )

    # Dates
    manufacturing_date = models.DateField()
    expiry_date = models.DateField()

    # Quantities
    quantity_manufactured = models.PositiveIntegerField(default=0)
    quantity_sent_to_distributors = models.PositiveIntegerField(default=0)

    # Status
    batch_status = models.CharField(
        max_length=15,
        choices=BATCH_STATUS_CHOICES,
        default='active'
    )

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['expiry_date']
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'

    def __str__(self):
        return f"{self.batch_number} — {self.product.product_name}"

    def save(self, *args, **kwargs):
        # Auto-set batch status based on expiry date
        today = timezone.now().date()
        if self.expiry_date <= today:
            self.batch_status = 'expired'
        elif self.expiry_date <= today + timedelta(days=90):
            self.batch_status = 'near_expiry'
        else:
            self.batch_status = 'active'
        super().save(*args, **kwargs)

    @property
    def quantity_available_in_company(self):
        """Stock remaining at company warehouse (not yet dispatched)."""
        return max(0, self.quantity_manufactured - self.quantity_sent_to_distributors)

    @property
    def days_to_expiry(self):
        today = timezone.now().date()
        delta = self.expiry_date - today
        return delta.days

    @property
    def is_near_expiry(self):
        return 0 < self.days_to_expiry <= 90

    @property
    def is_six_months_alert(self):
        return 90 < self.days_to_expiry <= 180


class CompanyStock(models.Model):
    """
    Company warehouse stock tracker.
    Aggregated view of available inventory per product/batch.
    Updated when batches are dispatched to distributors.
    """

    WAREHOUSE_CHOICES = [
        ('main', 'Main Warehouse'),
        ('cold_storage', 'Cold Storage'),
        ('secondary', 'Secondary Warehouse'),
    ]

    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='company_stocks'
    )
    batch = models.OneToOneField(
        BatchManagement,
        on_delete=models.CASCADE,
        related_name='company_stock'
    )
    warehouse_location = models.CharField(
        max_length=20,
        choices=WAREHOUSE_CHOICES,
        default='main'
    )

    # Thresholds for alerts
    low_stock_threshold = models.PositiveIntegerField(
        default=100,
        help_text='Alert when available stock falls below this number'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product__product_name']
        verbose_name = 'Company Stock'
        verbose_name_plural = 'Company Stock'

    def __str__(self):
        return f"{self.product.product_name} — {self.batch.batch_number}"

    @property
    def available_stock(self):
        return self.batch.quantity_available_in_company

    @property
    def is_low_stock(self):
        return self.available_stock <= self.low_stock_threshold

    @property
    def is_expired(self):
        return self.batch.batch_status == 'expired'

    @property
    def is_near_expiry(self):
        return self.batch.batch_status == 'near_expiry'