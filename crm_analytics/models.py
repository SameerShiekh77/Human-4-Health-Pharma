from django.db import models
from django.utils import timezone
from crm_products.models import ProductMaster, Division
from crm_sales.models import MedicalRepresentative, Region, Area
from crm_distributors.models import Distributor
from crm_doctors.models import Doctor


# ============================================================
# CRM ANALYTICS APP — crm_analytics/models.py
# Handles: Performance snapshots, KPI tracking, Expiry Alerts
# These models store pre-computed / summarized data for dashboards.
# Real-time metrics are computed via queries in views/services.
# ============================================================


class MRPerformanceSnapshot(models.Model):
    """
    Monthly performance summary for each Medical Representative.
    Populated by a scheduled management command or Celery task.
    Feeds the MR Performance Dashboard.
    """

    mr = models.ForeignKey(
        MedicalRepresentative,
        on_delete=models.CASCADE,
        related_name='performance_snapshots'
    )

    snapshot_month = models.DateField(
        help_text='Set to the 1st of the month being summarized'
    )

    # Visit metrics
    total_visits = models.PositiveIntegerField(default=0)
    gps_verified_visits = models.PositiveIntegerField(default=0)
    total_doctors_covered = models.PositiveIntegerField(default=0)
    unique_doctors_visited = models.PositiveIntegerField(default=0)

    # Prescription metrics
    total_prescription_value_generated = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text='Sum of estimated prescription values from all visits'
    )
    total_investment_given = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    # Efficiency scores
    gps_verified_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='% of visits with GPS verification'
    )
    working_efficiency_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='Composite score (0–100)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('mr', 'snapshot_month')
        ordering = ['-snapshot_month', 'mr__name']
        verbose_name = 'MR Performance Snapshot'
        verbose_name_plural = 'MR Performance Snapshots'

    def __str__(self):
        return f"{self.mr.name} — {self.snapshot_month.strftime('%b %Y')}"

    @property
    def roi(self):
        """ROI = Revenue Generated − Investment Given"""
        return float(self.total_prescription_value_generated) - float(self.total_investment_given)

    def compute_gps_percentage(self):
        if self.total_visits > 0:
            self.gps_verified_percentage = round(
                (self.gps_verified_visits / self.total_visits) * 100, 2
            )
        else:
            self.gps_verified_percentage = 0.00


class DoctorPerformanceSnapshot(models.Model):
    """
    Monthly ROI snapshot per doctor.
    Tracks investment vs estimated prescription revenue generated.
    """

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='performance_snapshots'
    )
    snapshot_month = models.DateField()

    estimated_prescription_per_month = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    total_investment_given = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    total_visits_received = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('doctor', 'snapshot_month')
        ordering = ['-snapshot_month']
        verbose_name = 'Doctor Performance Snapshot'
        verbose_name_plural = 'Doctor Performance Snapshots'

    def __str__(self):
        return (
            f"Dr. {self.doctor.doctor_name} — "
            f"{self.snapshot_month.strftime('%b %Y')}"
        )

    @property
    def roi(self):
        """ROI Formula: Revenue Generated − Investment Given"""
        return float(self.estimated_prescription_per_month) - float(self.total_investment_given)


class DistributorPerformanceSnapshot(models.Model):
    """
    Monthly performance summary per distributor.
    Aggregated from DistributorStockEntry and DistributorSalesValue.
    """

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.CASCADE,
        related_name='performance_snapshots'
    )
    snapshot_month = models.DateField()

    total_sales_value = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00
    )
    total_units_sold = models.PositiveIntegerField(default=0)
    total_unsold_stock = models.PositiveIntegerField(default=0)
    total_expired_stock = models.PositiveIntegerField(default=0)

    efficiency_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='% of received stock that was sold (not expired or unsold)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('distributor', 'snapshot_month')
        ordering = ['-snapshot_month']
        verbose_name = 'Distributor Performance Snapshot'
        verbose_name_plural = 'Distributor Performance Snapshots'

    def __str__(self):
        return (
            f"{self.distributor.distributor_name} — "
            f"{self.snapshot_month.strftime('%b %Y')}"
        )


class ProductPerformanceSnapshot(models.Model):
    """
    Monthly product-level sales performance.
    Broken down by region, distributor, and MR dimensions.
    """

    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='performance_snapshots'
    )
    snapshot_month = models.DateField()

    # Optional drill-down dimensions (null = totals across all)
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_snapshots'
    )
    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_snapshots'
    )
    mr = models.ForeignKey(
        MedicalRepresentative,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_snapshots'
    )

    units_sold = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    growth_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        help_text='Month-over-month growth %'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-snapshot_month', 'product__product_name']
        verbose_name = 'Product Performance Snapshot'
        verbose_name_plural = 'Product Performance Snapshots'

    def __str__(self):
        return (
            f"{self.product.product_name} — "
            f"{self.snapshot_month.strftime('%b %Y')}"
        )


# ============================================================
# EXPIRY ALERT SYSTEM
# ============================================================

class ExpiryAlert(models.Model):
    """
    System-generated expiry alerts for company stock, distributor stock, and batches.
    Created automatically by scheduled tasks (Celery / management command).
    """

    ALERT_TYPE_CHOICES = [
        ('6_months', '6 Months Warning'),
        ('3_months', '3 Months Warning'),
        ('1_month', '1 Month Warning'),
        ('expired', 'Expired'),
    ]

    SOURCE_CHOICES = [
        ('company_stock', 'Company Stock'),
        ('distributor_stock', 'Distributor Stock'),
        ('batch', 'Batch'),
    ]

    RECIPIENT_CHOICES = [
        ('admin', 'Admin'),
        ('sales_manager', 'Sales Manager'),
        ('distributor', 'Distributor'),
    ]

    alert_type = models.CharField(max_length=15, choices=ALERT_TYPE_CHOICES)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)

    # Generic FK-style fields (flexible for company/distributor/batch)
    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='expiry_alerts'
    )
    batch_number = models.CharField(max_length=50)
    expiry_date = models.DateField()
    quantity_at_risk = models.PositiveIntegerField(default=0)

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expiry_alerts',
        help_text='Populated when source is distributor_stock'
    )

    recipient = models.CharField(max_length=20, choices=RECIPIENT_CHOICES)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.CharField(max_length=150, blank=True, null=True)

    alert_sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-alert_sent_at']
        verbose_name = 'Expiry Alert'
        verbose_name_plural = 'Expiry Alerts'

    def __str__(self):
        return (
            f"{self.alert_type} — {self.product.product_name} "
            f"(Batch: {self.batch_number}) → {self.recipient}"
        )

    def acknowledge(self, user_name: str):
        self.is_acknowledged = True
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user_name
        self.save(update_fields=['is_acknowledged', 'acknowledged_at', 'acknowledged_by'])