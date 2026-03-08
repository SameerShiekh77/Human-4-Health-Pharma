## ── crm_doctors/forms.py ────────────────────────────────────

from django import forms
from django.forms import inlineformset_factory
from .models import (Doctor, DoctorVisit, VisitProductDetail,
                     DoctorInvestment, CompetitorInfo, PharmacyReference)


class DoctorForm(forms.ModelForm):
    class Meta:
        model  = Doctor
        fields = [
            'doctor_name', 'specialty', 'qualification',
            'hospital_name', 'clinic_name', 'city', 'area',
            'contact_number', 'email',
            'estimated_patients_per_day', 'estimated_prescription_potential',
            'assigned_mrs', 'status',
        ]
        widgets = {
            'doctor_name':    forms.TextInput(attrs={'placeholder': 'Full Name (no Dr. prefix)'}),
            'specialty':      forms.TextInput(attrs={'placeholder': 'e.g., Cardiologist'}),
            'qualification':  forms.TextInput(attrs={'placeholder': 'e.g., MBBS, FCPS'}),
            'hospital_name':  forms.TextInput(attrs={'placeholder': 'Hospital / Institution Name'}),
            'clinic_name':    forms.TextInput(attrs={'placeholder': 'Private Clinic Name'}),
            'contact_number': forms.TextInput(attrs={'placeholder': '+92 300 0000000'}),
            'email':          forms.EmailInput(attrs={'placeholder': 'doctor@example.com'}),
            'estimated_patients_per_day':    forms.NumberInput(attrs={'placeholder': '0'}),
            'estimated_prescription_potential': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
            'assigned_mrs':   forms.SelectMultiple(attrs={'size': '5'}),
        }


class DoctorVisitForm(forms.ModelForm):
    class Meta:
        model  = DoctorVisit
        fields = [
            'mr', 'doctor', 'visit_date', 'visit_time',
            'hospital_clinic_name', 'visit_type',
            'gps_latitude', 'gps_longitude', 'gps_address', 'is_gps_verified',
            'next_follow_up_date', 'remarks',
        ]
        widgets = {
            'visit_date':          forms.DateInput(attrs={'type': 'date'}),
            'visit_time':          forms.TimeInput(attrs={'type': 'time'}),
            'hospital_clinic_name':forms.TextInput(attrs={'placeholder': 'Hospital or Clinic Name'}),
            'gps_latitude':        forms.HiddenInput(),
            'gps_longitude':       forms.HiddenInput(),
            'gps_address':         forms.TextInput(attrs={'placeholder': 'Auto-filled from GPS', 'readonly': True}),
            'next_follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks':             forms.Textarea(attrs={'rows': 3, 'placeholder': 'Visit notes, observations...'}),
            'is_gps_verified':     forms.HiddenInput(),
        }


class VisitProductDetailForm(forms.ModelForm):
    class Meta:
        model  = VisitProductDetail
        fields = [
            'product', 'samples_given', 'promotional_material_given',
            'estimated_units_prescribed_per_day',
            'estimated_units_prescribed_per_month',
            'estimated_value_per_month',
        ]
        widgets = {
            'promotional_material_given':        forms.TextInput(attrs={'placeholder': 'e.g., Brochures, Pen'}),
            'samples_given':                     forms.NumberInput(attrs={'placeholder': '0'}),
            'estimated_units_prescribed_per_day':forms.NumberInput(attrs={'placeholder': '0'}),
            'estimated_units_prescribed_per_month':forms.NumberInput(attrs={'placeholder': '0'}),
            'estimated_value_per_month':         forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
        }


class DoctorInvestmentForm(forms.ModelForm):
    class Meta:
        model  = DoctorInvestment
        fields = ['investment_type', 'amount', 'description']
        widgets = {
            'amount':      forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'placeholder': 'Brief description'}),
        }


class CompetitorInfoForm(forms.ModelForm):
    class Meta:
        model  = CompetitorInfo
        fields = ['competitor_product_name', 'competitor_company', 'notes']
        widgets = {
            'competitor_product_name': forms.TextInput(attrs={'placeholder': 'Competitor Product'}),
            'competitor_company':      forms.TextInput(attrs={'placeholder': 'Company Name'}),
            'notes':                   forms.TextInput(attrs={'placeholder': 'Notes'}),
        }


class PharmacyReferenceForm(forms.ModelForm):
    class Meta:
        model  = PharmacyReference
        fields = ['store_name', 'store_location']
        widgets = {
            'store_name':     forms.TextInput(attrs={'placeholder': 'Medical Store Name'}),
            'store_location': forms.TextInput(attrs={'placeholder': 'Area / Address'}),
        }


# Inline Formsets
VisitProductDetailFormSet = inlineformset_factory(
    DoctorVisit, VisitProductDetail,
    form=VisitProductDetailForm,
    extra=1, can_delete=True, min_num=0
)

DoctorInvestmentFormSet = inlineformset_factory(
    DoctorVisit, DoctorInvestment,
    form=DoctorInvestmentForm,
    extra=1, can_delete=True, min_num=0
)

CompetitorInfoFormSet = inlineformset_factory(
    DoctorVisit, CompetitorInfo,
    form=CompetitorInfoForm,
    extra=1, can_delete=True, min_num=0
)

PharmacyReferenceFormSet = inlineformset_factory(
    DoctorVisit, PharmacyReference,
    form=PharmacyReferenceForm,
    extra=1, can_delete=True, min_num=0
)
