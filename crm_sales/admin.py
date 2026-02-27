
# crm_sales/admin.py
from django.contrib import admin
from .models import Region, Area, MedicalRepresentative

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['region_id', 'region_name', 'division', 'regional_manager']
    list_filter = ['division']
    readonly_fields = ['region_id']

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['area_id', 'area_name', 'region', 'area_manager']
    list_filter = ['region']
    readonly_fields = ['area_id']

@admin.register(MedicalRepresentative)
class MedicalRepresentativeAdmin(admin.ModelAdmin):
    list_display = ['mr_id', 'name', 'phone_number', 'division',
                    'region', 'area', 'status']
    search_fields = ['name', 'cnic', 'phone_number']
    list_filter = ['division', 'region', 'status']
    readonly_fields = ['mr_id']
