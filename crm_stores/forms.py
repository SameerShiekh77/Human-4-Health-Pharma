
## ── crm_stores/forms.py ─────────────────────────────────────

from django import forms
from .models import MedicalStore, StoreProductTracking


class MedicalStoreForm(forms.ModelForm):
    class Meta:
        model  = MedicalStore
        fields = [
            'store_name', 'owner_name', 'phone', 'address', 'area',
            'gps_latitude', 'gps_longitude', 'linked_doctors',
            'distributor', 'drug_license_number', 'status',
        ]
        widgets = {
            'store_name':       forms.TextInput(attrs={'placeholder': 'Store / Pharmacy Name'}),
            'owner_name':       forms.TextInput(attrs={'placeholder': 'Owner Name'}),
            'phone':            forms.TextInput(attrs={'placeholder': '+92 300 0000000'}),
            'address':          forms.Textarea(attrs={'rows': 2}),
            'drug_license_number': forms.TextInput(attrs={'placeholder': 'Drug License No.'}),
            'gps_latitude':     forms.HiddenInput(),
            'gps_longitude':    forms.HiddenInput(),
            'linked_doctors':   forms.SelectMultiple(attrs={'size': '5'}),
        }


class StoreProductTrackingForm(forms.ModelForm):
    class Meta:
        model  = StoreProductTracking
        fields = ['product', 'availability', 'monthly_sales_estimate', 'monthly_revenue_estimate']
        widgets = {
            'monthly_sales_estimate':   forms.NumberInput(attrs={'placeholder': '0'}),
            'monthly_revenue_estimate': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
        }

