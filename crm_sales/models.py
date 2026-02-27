from django.db import models
from django.contrib.auth.models import User
from crm_products.models import Division


# ============================================================
# CRM SALES APP — crm_sales/models.py
# Handles: Region → Area → Medical Representative hierarchy
# Division is defined in crm_products to avoid circular imports
# ============================================================


class Region(models.Model):
    """
    Geographic sales region, belonging to a Division.
    Managed by a Regional Manager.
    """

    region_id = models.CharField(max_length=20, unique=True, editable=False)
    region_name = models.CharField(max_length=100)
    division = models.ForeignKey(
        Division,
        on_delete=models.CASCADE,
        related_name='regions'
    )
    regional_manager = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['region_name']
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'

    def __str__(self):
        return f"{self.region_name} ({self.division.name})"

    def save(self, *args, **kwargs):
        if not self.region_id:
            last = Region.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.region_id = f"REG-{next_id:04d}"
        super().save(*args, **kwargs)


class Area(models.Model):
    """
    Sales area within a Region, managed by an Area Manager.
    """

    area_id = models.CharField(max_length=20, unique=True, editable=False)
    area_name = models.CharField(max_length=100)
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='areas'
    )
    area_manager = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['area_name']
        verbose_name = 'Area'
        verbose_name_plural = 'Areas'

    def __str__(self):
        return f"{self.area_name} — {self.region.region_name}"

    def save(self, *args, **kwargs):
        if not self.area_id:
            last = Area.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.area_id = f"AREA-{next_id:04d}"
        super().save(*args, **kwargs)


class MedicalRepresentative(models.Model):
    """
    Medical Representative (MR) — field force who visits doctors.
    Linked to a Django User for login access.
    Hierarchy: Division → Region → Area → MR
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mr_profile',
        help_text='Linked login account for MR app access'
    )

    mr_id = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=150)
    cnic = models.CharField(
        max_length=15,
        unique=True,
        verbose_name='CNIC',
        help_text='Format: 12345-1234567-1'
    )
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Assignment
    division = models.ForeignKey(
        Division,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mrs'
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mrs'
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mrs'
    )

    date_of_joining = models.DateField(blank=True, null=True)
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Monthly salary in PKR'
    )

    profile_image = models.ImageField(
        upload_to='crm/mr_profiles/',
        blank=True,
        null=True
    )

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Medical Representative'
        verbose_name_plural = 'Medical Representatives'

    def __str__(self):
        return f"{self.name} ({self.mr_id})"

    def save(self, *args, **kwargs):
        if not self.mr_id:
            last = MedicalRepresentative.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.mr_id = f"MR-{next_id:05d}"
        super().save(*args, **kwargs)

    @property
    def full_hierarchy(self):
        parts = []
        if self.division:
            parts.append(self.division.name)
        if self.region:
            parts.append(self.region.region_name)
        if self.area:
            parts.append(self.area.area_name)
        parts.append(self.name)
        return " → ".join(parts)