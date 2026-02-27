from django.db import models
from crm_products.models import ProductMaster
from crm_sales.models import MedicalRepresentative, Area


# ============================================================
# CRM DOCTORS APP — crm_doctors/models.py
# Handles: Doctor Profile + Doctor Visit Entry (GPS + investment)
# ============================================================


class Doctor(models.Model):
    """
    Doctor profile — the primary target of MR field visits.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    doctor_id = models.CharField(max_length=20, unique=True, editable=False)
    doctor_name = models.CharField(max_length=150)
    specialty = models.CharField(max_length=150)
    qualification = models.CharField(max_length=200, blank=True, null=True)

    hospital_name = models.CharField(max_length=200, blank=True, null=True)
    clinic_name = models.CharField(max_length=200, blank=True, null=True)

    city = models.CharField(max_length=100)
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctors'
    )

    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Prescription potential
    estimated_patients_per_day = models.PositiveIntegerField(
        default=0,
        help_text='Approximate daily patient footfall'
    )
    estimated_prescription_potential = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Estimated monthly revenue potential in PKR'
    )

    # Assigned MRs (many-to-many — one doctor can be covered by multiple MRs)
    assigned_mrs = models.ManyToManyField(
        MedicalRepresentative,
        blank=True,
        related_name='assigned_doctors'
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['doctor_name']
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'

    def __str__(self):
        return f"Dr. {self.doctor_name} — {self.specialty}"

    def save(self, *args, **kwargs):
        if not self.doctor_id:
            last = Doctor.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.doctor_id = f"DOC-{next_id:05d}"
        super().save(*args, **kwargs)


class VisitProductDetail(models.Model):
    """
    Products discussed during a single doctor visit.
    Embedded inside DoctorVisit via ForeignKey.
    """

    visit = models.ForeignKey(
        'DoctorVisit',
        on_delete=models.CASCADE,
        related_name='product_details'
    )
    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='visit_product_details'
    )
    samples_given = models.PositiveIntegerField(default=0)
    promotional_material_given = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='e.g., Brochures, Pens, Notepad'
    )

    # Prescription estimation
    estimated_units_prescribed_per_day = models.PositiveIntegerField(default=0)
    estimated_units_prescribed_per_month = models.PositiveIntegerField(default=0)
    estimated_value_per_month = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Estimated monthly prescription value in PKR'
    )

    class Meta:
        verbose_name = 'Visit Product Detail'
        verbose_name_plural = 'Visit Product Details'

    def __str__(self):
        return f"{self.product.product_name} @ Visit #{self.visit.id}"


class CompetitorInfo(models.Model):
    """
    Competitor products observed / reported during a visit.
    """

    visit = models.ForeignKey(
        'DoctorVisit',
        on_delete=models.CASCADE,
        related_name='competitor_info'
    )
    competitor_product_name = models.CharField(max_length=200)
    competitor_company = models.CharField(max_length=200)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Competitor Info'
        verbose_name_plural = 'Competitor Info'

    def __str__(self):
        return f"{self.competitor_product_name} by {self.competitor_company}"


class DoctorInvestment(models.Model):
    """
    Investment / promotional spend made on a doctor during a visit.
    Used in ROI calculation: Revenue Generated − Investment Given.
    """

    INVESTMENT_TYPE_CHOICES = [
        ('meeting', 'Meeting'),
        ('sponsorship', 'Sponsorship'),
        ('gifts', 'Gifts'),
        ('conference', 'Conference'),
        ('dinner', 'Dinner / Lunch'),
        ('samples', 'Samples'),
        ('other', 'Other'),
    ]

    visit = models.ForeignKey(
        'DoctorVisit',
        on_delete=models.CASCADE,
        related_name='investments'
    )
    investment_type = models.CharField(
        max_length=15,
        choices=INVESTMENT_TYPE_CHOICES
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Amount in PKR'
    )
    description = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        verbose_name = 'Doctor Investment'
        verbose_name_plural = 'Doctor Investments'

    def __str__(self):
        return f"{self.investment_type} — PKR {self.amount}"


class PharmacyReference(models.Model):
    """
    Medical stores / pharmacies where a doctor sends patients.
    Captured during visit entry for store-level tracking.
    """

    visit = models.ForeignKey(
        'DoctorVisit',
        on_delete=models.CASCADE,
        related_name='pharmacy_references'
    )
    store_name = models.CharField(max_length=200)
    store_location = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        verbose_name = 'Pharmacy Reference'
        verbose_name_plural = 'Pharmacy References'

    def __str__(self):
        return self.store_name


class DoctorVisit(models.Model):
    """
    **MOST IMPORTANT MODEL**
    Doctor visit entry submitted by an MR from the field.
    Includes GPS tracking, product details, investments, and competitor data.
    """

    VISIT_TYPE_CHOICES = [
        ('new_visit', 'New Visit'),
        ('follow_up', 'Follow Up'),
        ('emergency', 'Emergency Visit'),
    ]

    # Basic Info (MR auto-populated from request.user)
    mr = models.ForeignKey(
        MedicalRepresentative,
        on_delete=models.CASCADE,
        related_name='doctor_visits'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='visits'
    )

    visit_date = models.DateField()
    visit_time = models.TimeField()
    hospital_clinic_name = models.CharField(max_length=200, blank=True, null=True)

    visit_type = models.CharField(
        max_length=15,
        choices=VISIT_TYPE_CHOICES,
        default='follow_up'
    )

    # GPS Location Tracking (anti-fraud)
    gps_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    gps_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    gps_address = models.TextField(
        blank=True,
        null=True,
        help_text='Auto-fetched address from coordinates'
    )
    is_gps_verified = models.BooleanField(
        default=False,
        help_text='True when GPS coordinates were captured at time of submission'
    )

    # Follow-up scheduling
    next_follow_up_date = models.DateField(blank=True, null=True)

    # General remarks
    remarks = models.TextField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date', '-visit_time']
        verbose_name = 'Doctor Visit'
        verbose_name_plural = 'Doctor Visits'

    def __str__(self):
        return (
            f"Visit by {self.mr.name} → Dr. {self.doctor.doctor_name} "
            f"on {self.visit_date}"
        )

    @property
    def total_investment(self):
        """Sum of all investment amounts for this visit."""
        return sum(
            float(inv.amount)
            for inv in self.investments.all()
        )

    @property
    def total_estimated_value(self):
        """Sum of estimated prescription values from all products discussed."""
        return sum(
            float(pd.estimated_value_per_month)
            for pd in self.product_details.all()
        )