## ── crm_distributors/forms.py ──────────────────────────────

from django import forms
from .models import Distributor, DistributorStockEntry, DistributorSalesValue


class DistributorForm(forms.ModelForm):
    class Meta:
        model  = Distributor
        fields = [
            'distributor_name', 'owner_name', 'contact_number', 'email',
            'address', 'city', 'region', 'license_number', 'ntn_number',
            'credit_limit', 'status',
        ]
        widgets = {
            'distributor_name': forms.TextInput(attrs={'placeholder': 'Company / Trading Name'}),
            'owner_name':       forms.TextInput(attrs={'placeholder': 'Owner Full Name'}),
            'contact_number':   forms.TextInput(attrs={'placeholder': '+92 300 0000000'}),
            'email':            forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'address':          forms.Textarea(attrs={'rows': 2}),
            'license_number':   forms.TextInput(attrs={'placeholder': 'Drug License Number'}),
            'ntn_number':       forms.TextInput(attrs={'placeholder': 'National Tax Number'}),
            'credit_limit':     forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
        }


class DistributorStockEntryForm(forms.ModelForm):
    class Meta:
        model  = DistributorStockEntry
        fields = [
            'distributor', 'product', 'batch',
            'opening_stock', 'received_quantity', 'sold_quantity',
            'expired_quantity', 'near_expiry_quantity',
            'report_period_start', 'report_period_end', 'notes',
        ]
        widgets = {
            'report_period_start': forms.DateInput(attrs={'type': 'date'}),
            'report_period_end':   forms.DateInput(attrs={'type': 'date'}),
            'notes':               forms.Textarea(attrs={'rows': 2}),
            'opening_stock':       forms.NumberInput(attrs={'placeholder': '0'}),
            'received_quantity':   forms.NumberInput(attrs={'placeholder': '0'}),
            'sold_quantity':       forms.NumberInput(attrs={'placeholder': '0'}),
            'expired_quantity':    forms.NumberInput(attrs={'placeholder': '0'}),
            'near_expiry_quantity':forms.NumberInput(attrs={'placeholder': '0'}),
        }


class DistributorSalesValueForm(forms.ModelForm):
    class Meta:
        model  = DistributorSalesValue
        fields = ['distributor', 'product', 'quantity_sold', 'price_per_unit', 'sale_date']
        widgets = {
            'sale_date':      forms.DateInput(attrs={'type': 'date'}),
            'quantity_sold':  forms.NumberInput(attrs={'placeholder': '0'}),
            'price_per_unit': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
        }