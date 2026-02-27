
# crm_stores/admin.py
from django.contrib import admin
from .models import MedicalStore, StoreProductTracking

@admin.register(MedicalStore)
class MedicalStoreAdmin(admin.ModelAdmin):
    list_display = ['store_id', 'store_name', 'owner_name', 'area',
                    'distributor', 'status']
    search_fields = ['store_name', 'owner_name']
    list_filter = ['status', 'area', 'distributor']
    readonly_fields = ['store_id']

@admin.register(StoreProductTracking)
class StoreProductTrackingAdmin(admin.ModelAdmin):
    list_display = ['store', 'product', 'availability', 'monthly_sales_estimate']
    list_filter = ['availability']
