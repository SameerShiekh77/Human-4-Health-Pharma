from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from crm_products.models import Division, ProductMaster
from crm_sales.models import Region, Area, MedicalRepresentative
from crm_doctors.models import (
    Doctor,
    DoctorPracticeLocation,
    DoctorVisit,
    VisitProductDetail,
    DoctorInvestment,
    CompetitorInfo,
    PharmacyReference,
)


User = get_user_model()


class Command(BaseCommand):
    help = "Seed local CRM test data for doctor visit flows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete previously seeded test data before creating new data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_seed_data()

        territory = Division.objects.get_or_create(
            name="North Territory Test",
            defaults={"manager_name": "Test Territory Manager", "is_active": True},
        )[0]

        region = Region.objects.get_or_create(
            region_name="Lahore North Test",
            division=territory,
            defaults={"regional_manager": "Test Regional Manager", "is_active": True},
        )[0]

        area = Area.objects.get_or_create(
            area_name="Gulberg Test Area",
            region=region,
            defaults={"area_manager": "Test Area Manager", "is_active": True},
        )[0]

        mr_user, _ = User.objects.get_or_create(
            username="testmr",
            defaults={"email": "testmr@example.com"},
        )
        if not mr_user.first_name:
            mr_user.first_name = "Test"
            mr_user.last_name = "MR"
            mr_user.set_password("test12345")
            mr_user.save(update_fields=["first_name", "last_name", "password"])

        mr = MedicalRepresentative.objects.get_or_create(
            name="Test MR",
            cnic="12345-1234567-1",
            defaults={
                "user": mr_user,
                "phone_number": "+92 300 1111111",
                "email": "testmr@example.com",
                "address": "Test MR Office",
                "division": territory,
                "region": region,
                "area": area,
                "status": "active",
            },
        )[0]

        doctor, _ = Doctor.objects.get_or_create(
            doctor_name="Dr. Ali Hassan",
            specialty="General Physician",
            defaults={
                "qualification": "MBBS, FCPS",
                "hospital_name": "City Care Hospital",
                "clinic_name": "Ali Clinic",
                "city": "Lahore",
                "area": area,
                "contact_number": "+92 321 2222222",
                "email": "ali.hassan@example.com",
                "estimated_patients_per_day": 45,
                "estimated_prescription_potential": 85000.00,
                "status": "active",
            },
        )
        doctor.assigned_mrs.add(mr)

        main_location, _ = DoctorPracticeLocation.objects.get_or_create(
            doctor=doctor,
            location_name="City Care Hospital",
            defaults={
                "location_type": "hospital",
                "address": "Main Boulevard, Lahore",
                "is_active": True,
            },
        )
        clinic_location, _ = DoctorPracticeLocation.objects.get_or_create(
            doctor=doctor,
            location_name="Ali Clinic",
            defaults={
                "location_type": "clinic",
                "address": "Model Town, Lahore",
                "is_active": True,
            },
        )

        product, _ = ProductMaster.objects.get_or_create(
            product_name="Amoxicillin 500mg",
            generic_name="Amoxicillin",
            brand_name="Amoxi-Test",
            defaults={
                "category": "tablet",
                "division": territory,
                "strength": "500mg",
                "packing_size": "10x10",
                "manufacturing_cost_per_unit": 40.00,
                "trade_price": 82.36,
                "retail_price": 100.00,
                "distributor_price": 88.00,
                "status": "active",
                "description": "Seed product for local testing.",
            },
        )

        today = timezone.localdate()
        visit1 = self._create_visit(
            mr=mr,
            doctor=doctor,
            location=main_location,
            visit_date=today - timedelta(days=2),
            visit_time=time(10, 30),
            status="new_visit",
            gps_offset=0.001,
            remarks="First test visit for popup history.",
            product=product,
        )
        visit2 = self._create_visit(
            mr=mr,
            doctor=doctor,
            location=clinic_location,
            visit_date=today - timedelta(days=1),
            visit_time=time(16, 15),
            status="follow_up",
            gps_offset=0.002,
            remarks="Second test visit, should appear as latest history.",
            product=product,
        )

        self.stdout.write(self.style.SUCCESS("Seeded local CRM test data successfully."))
        self.stdout.write(f"Territory: {territory.name}")
        self.stdout.write(f"Doctor: {doctor.doctor_name}")
        self.stdout.write(f"Practice locations: {main_location.location_name}, {clinic_location.location_name}")
        self.stdout.write(f"Visits created: {visit1.pk}, {visit2.pk}")

    def _create_visit(self, mr, doctor, location, visit_date, visit_time, status, gps_offset, remarks, product):
        visit = DoctorVisit.objects.create(
            mr=mr,
            doctor=doctor,
            visit_location=location,
            visit_date=visit_date,
            visit_time=visit_time,
            hospital_clinic_name=location.location_name,
            visit_type=status,
            gps_latitude=31.5204000 + gps_offset,
            gps_longitude=74.3587000 + gps_offset,
            gps_address=f"{location.location_name}, Lahore",
            is_gps_verified=True,
            next_follow_up_date=visit_date + timedelta(days=7),
            remarks=remarks,
        )

        VisitProductDetail.objects.create(
            visit=visit,
            product=product,
            samples_given=5,
            promotional_material_given="Brochures",
            estimated_units_prescribed_per_day=12,
            estimated_units_prescribed_per_month=360,
            estimated_value_per_month=18000.00,
        )

        DoctorInvestment.objects.create(
            visit=visit,
            investment_type="cash",
            amount=1500.00,
            description="Cash",
        )
        DoctorInvestment.objects.create(
            visit=visit,
            investment_type="other",
            amount=500.00,
            description="Flower Basket",
        )

        CompetitorInfo.objects.create(
            visit=visit,
            competitor_product_name="Cefixime 200mg",
            competitor_company="Competitor Pharma",
            notes="Frequently prescribed in the same segment.",
        )

        PharmacyReference.objects.create(
            visit=visit,
            store_name="Medicare Pharmacy",
            store_location="Near City Care Hospital",
        )

        return visit

    def _clear_seed_data(self):
        DoctorVisit.objects.filter(doctor__doctor_name="Dr. Ali Hassan").delete()
        DoctorPracticeLocation.objects.filter(doctor__doctor_name="Dr. Ali Hassan").delete()
        Doctor.objects.filter(doctor_name="Dr. Ali Hassan").delete()
        MedicalRepresentative.objects.filter(name="Test MR").delete()
        User.objects.filter(username="testmr").delete()
        ProductMaster.objects.filter(product_name="Amoxicillin 500mg").delete()
        Area.objects.filter(area_name="Gulberg Test Area").delete()
        Region.objects.filter(region_name="Lahore North Test").delete()
        Division.objects.filter(name="North Territory Test").delete()
