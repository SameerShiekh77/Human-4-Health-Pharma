
# crm_analytics/admin.py
from django.contrib import admin
from .models import (MRPerformanceSnapshot, DoctorPerformanceSnapshot,
                     DistributorPerformanceSnapshot, ProductPerformanceSnapshot,
                     ExpiryAlert)

@admin.register(MRPerformanceSnapshot)
class MRPerformanceSnapshotAdmin(admin.ModelAdmin):
    list_display = ['mr', 'snapshot_month', 'total_visits',
                    'gps_verified_percentage', 'total_prescription_value_generated',
                    'working_efficiency_score']
    list_filter = ['snapshot_month']

@admin.register(DoctorPerformanceSnapshot)
class DoctorPerformanceSnapshotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'snapshot_month', 'estimated_prescription_per_month',
                    'total_investment_given', 'roi']
    list_filter = ['snapshot_month']

@admin.register(ExpiryAlert)
class ExpiryAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'batch_number', 'expiry_date', 'alert_type',
                    'source', 'recipient', 'quantity_at_risk', 'is_acknowledged']
    list_filter = ['alert_type', 'source', 'recipient', 'is_acknowledged']
    search_fields = ['product__product_name', 'batch_number']
