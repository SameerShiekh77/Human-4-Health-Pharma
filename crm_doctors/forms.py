## ── crm_doctors/forms.py ────────────────────────────────────

from django import forms
from django.forms import inlineformset_factory
from .models import (Doctor, DoctorVisit, VisitProductDetail,
                     DoctorInvestment, CompetitorInfo, PharmacyReference,
                     DoctorPracticeLocation)


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
    LOCATION_MODE_CHOICES = [
        ('existing', 'Use Existing Location'),
        ('new', 'Add New Location'),
    ]

    location_mode = forms.ChoiceField(
        choices=LOCATION_MODE_CHOICES,
        initial='existing',
        widget=forms.RadioSelect
    )
    visit_location = forms.ModelChoiceField(
        queryset=DoctorPracticeLocation.objects.none(),
        required=False,
        empty_label='Select saved location'
    )
    new_location_name = forms.CharField(required=False)
    new_location_type = forms.ChoiceField(
        choices=DoctorPracticeLocation.LOCATION_TYPE_CHOICES,
        required=False,
        initial='clinic'
    )
    new_location_address = forms.CharField(required=False)

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
            'hospital_clinic_name':forms.HiddenInput(),
            'gps_latitude':        forms.HiddenInput(),
            'gps_longitude':       forms.HiddenInput(),
            'gps_address':         forms.TextInput(attrs={'placeholder': 'Auto-filled from GPS', 'readonly': True}),
            'next_follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks':             forms.Textarea(attrs={'rows': 3, 'placeholder': 'Visit notes, observations...'}),
            'is_gps_verified':     forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['new_location_name'].widget = forms.TextInput(
            attrs={'placeholder': 'e.g., City Medical Center'}
        )
        self.fields['new_location_address'].widget = forms.TextInput(
            attrs={'placeholder': 'Area / Address (optional)'}
        )

        doctor_id = None
        if self.is_bound:
            doctor_id = self.data.get('doctor')
        elif self.instance and self.instance.pk:
            doctor_id = self.instance.doctor_id
        else:
            doctor_id = self.initial.get('doctor')

        if doctor_id:
            self.fields['visit_location'].queryset = DoctorPracticeLocation.objects.filter(
                doctor_id=doctor_id,
                is_active=True
            ).order_by('location_name')

        if self.instance and self.instance.pk:
            if self.instance.visit_location_id:
                self.fields['location_mode'].initial = 'existing'
                self.fields['visit_location'].initial = self.instance.visit_location
            else:
                self.fields['location_mode'].initial = 'new'
                self.fields['new_location_name'].initial = self.instance.hospital_clinic_name

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get('doctor')
        mode = cleaned.get('location_mode')
        location = cleaned.get('visit_location')
        new_name = (cleaned.get('new_location_name') or '').strip()

        if not doctor:
            return cleaned

        if mode == 'existing':
            if not location:
                self.add_error('visit_location', 'Please select an existing location.')
            elif location.doctor_id != doctor.id:
                self.add_error('visit_location', 'Selected location does not belong to this doctor.')
        else:
            if not new_name:
                self.add_error('new_location_name', 'Please enter a new location name.')

        return cleaned

    def save(self, commit=True):
        visit = super().save(commit=False)

        mode = self.cleaned_data.get('location_mode')
        selected_location = self.cleaned_data.get('visit_location')

        if mode == 'existing' and selected_location:
            visit.visit_location = selected_location
            visit.hospital_clinic_name = selected_location.location_name
        elif mode == 'new':
            if commit:
                location = DoctorPracticeLocation.objects.create(
                    doctor=self.cleaned_data['doctor'],
                    location_name=(self.cleaned_data.get('new_location_name') or '').strip(),
                    location_type=self.cleaned_data.get('new_location_type') or 'clinic',
                    address=(self.cleaned_data.get('new_location_address') or '').strip() or None,
                )
                visit.visit_location = location
                visit.hospital_clinic_name = location.location_name
            else:
                visit.hospital_clinic_name = (self.cleaned_data.get('new_location_name') or '').strip() or None

        if commit:
            visit.save()
            self.save_m2m()

        return visit


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
            'description': forms.TextInput(attrs={'placeholder': 'Enter other investment name'}),
        }

    def clean(self):
        cleaned = super().clean()
        inv_type = cleaned.get('investment_type')
        desc = (cleaned.get('description') or '').strip()

        if inv_type == 'other' and not desc:
            self.add_error('description', 'Please enter the name for Others.')

        return cleaned


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
