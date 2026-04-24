
# crm_doctors/admin.py
from django.contrib import admin
from .models import (Doctor, DoctorVisit, VisitProductDetail,
                     CompetitorInfo, DoctorInvestment, PharmacyReference,
                     DoctorPracticeLocation)

class VisitProductDetailInline(admin.TabularInline):
    model = VisitProductDetail
    extra = 1

class CompetitorInfoInline(admin.TabularInline):
    model = CompetitorInfo
    extra = 1

class DoctorInvestmentInline(admin.TabularInline):
    model = DoctorInvestment
    extra = 1

class PharmacyReferenceInline(admin.TabularInline):
    model = PharmacyReference
    extra = 1

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['doctor_id', 'doctor_name', 'specialty', 'city',
                    'estimated_patients_per_day', 'status']
    search_fields = ['doctor_name', 'specialty', 'hospital_name']
    list_filter = ['specialty', 'status', 'area']
    readonly_fields = ['doctor_id']

@admin.register(DoctorVisit)
class DoctorVisitAdmin(admin.ModelAdmin):
    list_display = ['mr', 'doctor', 'visit_location', 'visit_date', 'visit_type',
                    'is_gps_verified', 'total_investment']
    list_filter = ['visit_type', 'is_gps_verified', 'visit_date']
    search_fields = ['mr__name', 'doctor__doctor_name']
    inlines = [
        VisitProductDetailInline,
        CompetitorInfoInline,
        DoctorInvestmentInline,
        PharmacyReferenceInline,
    ]


@admin.register(DoctorPracticeLocation)
class DoctorPracticeLocationAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'location_name', 'location_type', 'is_active']
    search_fields = ['doctor__doctor_name', 'location_name', 'address']
    list_filter = ['location_type', 'is_active']
