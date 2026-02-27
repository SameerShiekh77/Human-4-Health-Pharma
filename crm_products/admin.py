
# crm_products/admin.py
from django.contrib import admin
from .models import Division, ProductMaster, BatchManagement, CompanyStock

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ['division_id', 'name', 'manager_name', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']

@admin.register(ProductMaster)
class ProductMasterAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'product_name', 'generic_name', 'category',
                    'strength', 'retail_price', 'status']
    search_fields = ['product_name', 'generic_name', 'brand_name']
    list_filter = ['category', 'division', 'status']
    readonly_fields = ['product_id']

@admin.register(BatchManagement)
class BatchManagementAdmin(admin.ModelAdmin):
    list_display = ['batch_number', 'product', 'manufacturing_date',
                    'expiry_date', 'quantity_manufactured', 'batch_status',
                    'days_to_expiry']
    list_filter = ['batch_status', 'product']
    search_fields = ['batch_number', 'product__product_name']
    readonly_fields = ['batch_status']

@admin.register(CompanyStock)
class CompanyStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'batch', 'warehouse_location',
                    'available_stock', 'is_low_stock', 'is_near_expiry']
    list_filter = ['warehouse_location']