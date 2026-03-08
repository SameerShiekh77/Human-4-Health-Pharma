
## ── crm_sales/forms.py ──────────────────────────────────────

from django import forms
from .models import Region, Area, MedicalRepresentative


class RegionForm(forms.ModelForm):
    class Meta:
        model  = Region
        fields = ['region_name', 'division', 'regional_manager', 'is_active']
        widgets = {
            'region_name':      forms.TextInput(attrs={'placeholder': 'e.g., Karachi South'}),
            'regional_manager': forms.TextInput(attrs={'placeholder': 'Manager Name'}),
        }


class AreaForm(forms.ModelForm):
    class Meta:
        model  = Area
        fields = ['area_name', 'region', 'area_manager', 'is_active']
        widgets = {
            'area_name':    forms.TextInput(attrs={'placeholder': 'e.g., Gulshan Block 13'}),
            'area_manager': forms.TextInput(attrs={'placeholder': 'Manager Name'}),
        }


class MedicalRepresentativeForm(forms.ModelForm):
    class Meta:
        model  = MedicalRepresentative
        fields = [
            'name', 'cnic', 'phone_number', 'email', 'address',
            'division', 'region', 'area', 'date_of_joining',
            'salary', 'profile_image', 'status', 'user',
        ]
        widgets = {
            'name':           forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'cnic':           forms.TextInput(attrs={'placeholder': '12345-1234567-1'}),
            'phone_number':   forms.TextInput(attrs={'placeholder': '+92 300 0000000'}),
            'email':          forms.EmailInput(attrs={'placeholder': 'mr@example.com'}),
            'address':        forms.Textarea(attrs={'rows': 2}),
            'date_of_joining':forms.DateInput(attrs={'type': 'date'}),
            'salary':         forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
        }

