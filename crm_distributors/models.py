from django.db import models
from crm_products.models import ProductMaster, BatchManagement


# ============================================================
# CRM DISTRIBUTORS APP — crm_distributors/models.py
# Handles: Distributor Profile + Stock Entry + Sales Value
# ============================================================


class Distributor(models.Model):
    """
    Distributor profile — the entities that receive stock from the company
    and sell to pharmacies / medical stores.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    distributor_id = models.CharField(max_length=20, unique=True, editable=False)
    distributor_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)

    # Legal
    license_number = models.CharField(max_length=100, unique=True)
    ntn_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='NTN Number',
        help_text='National Tax Number'
    )

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    # Credit limit
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Maximum outstanding credit allowed (PKR)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['distributor_name']
        verbose_name = 'Distributor'
        verbose_name_plural = 'Distributors'

    def __str__(self):
        return f"{self.distributor_name} ({self.city})"

    def save(self, *args, **kwargs):
        if not self.distributor_id:
            last = Distributor.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.distributor_id = f"DIST-{next_id:04d}"
        super().save(*args, **kwargs)


class DistributorStockEntry(models.Model):
    """
    Monthly / periodic stock report submitted by each distributor.
    Tracks: opening → received → sold → expired → closing stock.
    Auto-calculates closing stock.
    """

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.CASCADE,
        related_name='stock_entries'
    )
    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='distributor_stock_entries'
    )
    batch = models.ForeignKey(
        BatchManagement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='distributor_stock_entries'
    )

    # Stock Quantities
    opening_stock = models.PositiveIntegerField(default=0)
    received_quantity = models.PositiveIntegerField(
        default=0,
        help_text='Stock received from company in this period'
    )
    sold_quantity = models.PositiveIntegerField(default=0)
    unsold_quantity = models.PositiveIntegerField(default=0)
    expired_quantity = models.PositiveIntegerField(default=0)
    near_expiry_quantity = models.PositiveIntegerField(default=0)

    # Period
    report_period_start = models.DateField()
    report_period_end = models.DateField()
    date_submitted = models.DateTimeField(auto_now_add=True)

    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Distributor Stock Entry'
        verbose_name_plural = 'Distributor Stock Entries'

    def __str__(self):
        return (
            f"{self.distributor.distributor_name} — "
            f"{self.product.product_name} ({self.report_period_end})"
        )

    @property
    def closing_stock(self):
        """
        Formula: Closing Stock = Opening + Received − Sold − Expired
        """
        return max(
            0,
            self.opening_stock + self.received_quantity
            - self.sold_quantity
            - self.expired_quantity
        )

    def save(self, *args, **kwargs):
        # Keep unsold_quantity in sync with closing stock before saving
        self.unsold_quantity = self.closing_stock
        super().save(*args, **kwargs)


class DistributorSalesValue(models.Model):
    """
    Financial value of sales recorded by/for a distributor in a period.
    Feeds into Distributor Performance Dashboard.
    """

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.CASCADE,
        related_name='sales_values'
    )
    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='distributor_sales_values'
    )
    quantity_sold = models.PositiveIntegerField(default=0)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    sale_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date']
        verbose_name = 'Distributor Sales Value'
        verbose_name_plural = 'Distributor Sales Values'

    def __str__(self):
        return (
            f"{self.distributor.distributor_name} — "
            f"{self.product.product_name} on {self.sale_date}"
        )

    @property
    def total_sales_value(self):
        """Total Sales Value = Quantity Sold × Price per Unit"""
        return float(self.quantity_sold) * float(self.price_per_unit)