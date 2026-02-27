from django.db import models
from crm_products.models import ProductMaster
from crm_sales.models import Area
from crm_distributors.models import Distributor
from crm_doctors.models import Doctor


# ============================================================
# CRM STORES APP — crm_stores/models.py
# Handles: Medical Store / Pharmacy Profile + Product Tracking
# ============================================================


class MedicalStore(models.Model):
    """
    Medical store / pharmacy profile.
    Linked to doctors who refer patients and to distributors who supply.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    store_id = models.CharField(max_length=20, unique=True, editable=False)
    store_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Location
    address = models.TextField()
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_stores'
    )

    # GPS for map visualization
    gps_latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    gps_longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )

    # Relationships
    linked_doctors = models.ManyToManyField(
        Doctor,
        blank=True,
        related_name='linked_stores',
        help_text='Doctors who refer patients to this store'
    )
    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_stores',
        help_text='Primary distributor supplying this store'
    )

    drug_license_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['store_name']
        verbose_name = 'Medical Store'
        verbose_name_plural = 'Medical Stores'

    def __str__(self):
        return f"{self.store_name} ({self.area})"

    def save(self, *args, **kwargs):
        if not self.store_id:
            last = MedicalStore.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.store_id = f"STORE-{next_id:05d}"
        super().save(*args, **kwargs)


class StoreProductTracking(models.Model):
    """
    Tracks product availability and monthly sales estimates
    at each medical store. Updated periodically by MR during visits.
    """

    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('out_of_stock', 'Out of Stock'),
        ('low_stock', 'Low Stock'),
    ]

    store = models.ForeignKey(
        MedicalStore,
        on_delete=models.CASCADE,
        related_name='product_trackings'
    )
    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='store_trackings'
    )

    availability = models.CharField(
        max_length=15,
        choices=AVAILABILITY_CHOICES,
        default='available'
    )
    monthly_sales_estimate = models.PositiveIntegerField(
        default=0,
        help_text='Estimated units sold per month at this store'
    )
    monthly_revenue_estimate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Estimated monthly revenue in PKR'
    )

    last_updated_by_mr = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text='MR name who last updated this record'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('store', 'product')
        ordering = ['store__store_name', 'product__product_name']
        verbose_name = 'Store Product Tracking'
        verbose_name_plural = 'Store Product Trackings'

    def __str__(self):
        return f"{self.product.product_name} @ {self.store.store_name}"