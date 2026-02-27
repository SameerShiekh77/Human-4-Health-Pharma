
# crm_distributors/admin.py
from django.contrib import admin
from .models import Distributor, DistributorStockEntry, DistributorSalesValue

@admin.register(Distributor)
class DistributorAdmin(admin.ModelAdmin):
    list_display = ['distributor_id', 'distributor_name', 'owner_name',
                    'city', 'region', 'status']
    search_fields = ['distributor_name', 'owner_name', 'license_number']
    list_filter = ['status', 'city', 'region']
    readonly_fields = ['distributor_id']

@admin.register(DistributorStockEntry)
class DistributorStockEntryAdmin(admin.ModelAdmin):
    list_display = ['distributor', 'product', 'opening_stock', 'received_quantity',
                    'sold_quantity', 'closing_stock', 'report_period_end']
    list_filter = ['distributor', 'product']
    readonly_fields = ['closing_stock']

@admin.register(DistributorSalesValue)
class DistributorSalesValueAdmin(admin.ModelAdmin):
    list_display = ['distributor', 'product', 'quantity_sold',
                    'price_per_unit', 'total_sales_value', 'sale_date']
    list_filter = ['distributor', 'product']
