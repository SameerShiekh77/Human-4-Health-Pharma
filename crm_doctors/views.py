## ── crm_doctors/views.py ────────────────────────────────────

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.auth_utils import crm_access_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.urls import reverse

from .models import (Doctor, DoctorVisit, VisitProductDetail,
                     CompetitorInfo, DoctorInvestment, PharmacyReference,
                     DoctorPracticeLocation)
from .forms import (DoctorForm, DoctorVisitForm,
                    VisitProductDetailFormSet, DoctorInvestmentFormSet,
                    CompetitorInfoFormSet, PharmacyReferenceFormSet)


# ─── DOCTOR ──────────────────────────────

@crm_access_required
def doctor_list(request):
    qs = Doctor.objects.select_related('area').prefetch_related('assigned_mrs')

    q        = request.GET.get('q', '')
    status   = request.GET.get('status', '')
    spec     = request.GET.get('specialty', '')

    if q:
        qs = qs.filter(
            Q(doctor_name__icontains=q) |
            Q(doctor_id__icontains=q) |
            Q(hospital_name__icontains=q) |
            Q(specialty__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if spec:
        qs = qs.filter(specialty__icontains=spec)

    specialties = Doctor.objects.values_list('specialty', flat=True).distinct().order_by('specialty')

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/doctors/doctor_list.html', {
        'page_obj':    page,
        'query':       q,
        'specialties': specialties,
        'total':       qs.count(),
        'active':      Doctor.objects.filter(status='active').count(),
        'export_url': reverse('crm_data_tools:export', args=['doctor']),
        'sample_url': reverse('crm_data_tools:sample', args=['doctor']),
        'import_url': reverse('crm_data_tools:import', args=['doctor']),
    })


@crm_access_required
def doctor_detail(request, pk):
    doctor  = get_object_or_404(Doctor, pk=pk)
    visits  = doctor.visits.select_related('mr').order_by('-visit_date')
    total_investment = sum(v.total_investment for v in visits)
    total_value      = sum(v.total_estimated_value for v in visits)

    paginator = Paginator(visits, 10)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/doctors/doctor_detail.html', {
        'doctor':           doctor,
        'visits_page':      page,
        'total_visits':     visits.count(),
        'total_investment': total_investment,
        'total_value':      total_value,
        'roi':              total_value - total_investment,
    })


@crm_access_required
def doctor_create(request):
    form = DoctorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Doctor profile created.')
        return redirect('crm_doctors:doctor_list')
    return render(request, 'crm/doctors/doctor_form.html', {'form': form, 'action': 'Add'})


@crm_access_required
def doctor_edit(request, pk):
    obj  = get_object_or_404(Doctor, pk=pk)
    form = DoctorForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Doctor profile updated.')
        return redirect('crm_doctors:doctor_detail', pk=pk)
    return render(request, 'crm/doctors/doctor_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@crm_access_required
def doctor_delete(request, pk):
    obj = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Doctor deleted.')
        return redirect('crm_doctors:doctor_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': f'Dr. {obj.doctor_name}'})


# ─── DOCTOR VISIT (MOST IMPORTANT) ───────

@crm_access_required
def visit_list(request):
    qs = DoctorVisit.objects.select_related('mr', 'doctor', 'visit_location').order_by('-visit_date', '-visit_time')

    q          = request.GET.get('q', '')
    mr_id      = request.GET.get('mr', '')
    gps        = request.GET.get('gps', '')
    visit_type = request.GET.get('type', '')
    date_from  = request.GET.get('date_from', '')
    date_to    = request.GET.get('date_to', '')

    if q:
        qs = qs.filter(
            Q(doctor__doctor_name__icontains=q) |
            Q(mr__name__icontains=q)
        )
    if mr_id:
        qs = qs.filter(mr_id=mr_id)
    if gps == '1':
        qs = qs.filter(is_gps_verified=True)
    elif gps == '0':
        qs = qs.filter(is_gps_verified=False)
    if visit_type:
        qs = qs.filter(visit_type=visit_type)
    if date_from:
        qs = qs.filter(visit_date__gte=date_from)
    if date_to:
        qs = qs.filter(visit_date__lte=date_to)

    from crm_sales.models import MedicalRepresentative
    mrs = MedicalRepresentative.objects.filter(status='active')

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/doctors/visit_list.html', {
        'page_obj':    page,
        'query':       q,
        'mrs':         mrs,
        'total':       qs.count(),
        'gps_total':   qs.filter(is_gps_verified=True).count(),
        'today_count': qs.filter(visit_date=__import__('django.utils.timezone', fromlist=['now']).now().date()).count()
            if False else DoctorVisit.objects.filter(
                visit_date=__import__('datetime').date.today()
            ).count(),
        'visit_types': DoctorVisit.VISIT_TYPE_CHOICES,
        'export_url': reverse('crm_data_tools:export', args=['doctor_visit']),
        'sample_url': reverse('crm_data_tools:sample', args=['doctor_visit']),
        'import_url': reverse('crm_data_tools:import', args=['doctor_visit']),
    })


@crm_access_required
def visit_detail(request, pk):
    visit = get_object_or_404(
        DoctorVisit.objects.select_related('mr', 'doctor', 'visit_location')
            .prefetch_related('product_details__product',
                              'investments',
                              'competitor_info',
                              'pharmacy_references'),
        pk=pk
    )
    return render(request, 'crm/doctors/visit_detail.html', {'visit': visit})


@crm_access_required
def visit_create(request):
    """
    Full visit entry form with inline formsets for:
    - Products discussed
    - Doctor investments
    - Competitor info
    - Pharmacy references
    GPS data captured via JavaScript Geolocation API on the template.
    """
    from crm_sales.models import MedicalRepresentative

    if request.method == 'POST':
        form             = DoctorVisitForm(request.POST)
        product_fs       = VisitProductDetailFormSet(request.POST, prefix='products')
        investment_fs    = DoctorInvestmentFormSet(request.POST, prefix='investments')
        competitor_fs    = CompetitorInfoFormSet(request.POST, prefix='competitors')
        pharmacy_fs      = PharmacyReferenceFormSet(request.POST, prefix='pharmacies')

        if (form.is_valid() and product_fs.is_valid() and
                investment_fs.is_valid() and competitor_fs.is_valid() and
                pharmacy_fs.is_valid()):

            visit = form.save()

            for fs in [product_fs, investment_fs, competitor_fs, pharmacy_fs]:
                instances = fs.save(commit=False)
                for inst in instances:
                    inst.visit = visit
                    inst.save()
                for deleted in fs.deleted_objects:
                    deleted.delete()

            messages.success(request, 'Visit recorded successfully!')
            return redirect('crm_doctors:visit_detail', pk=visit.pk)
    else:
        # Pre-fill MR from logged-in user if they are an MR
        initial = {}
        try:
            mr = request.user.mr_profile
            initial['mr'] = mr
        except Exception:
            pass

        form          = DoctorVisitForm(initial=initial)
        product_fs    = VisitProductDetailFormSet(prefix='products')
        investment_fs = DoctorInvestmentFormSet(prefix='investments')
        competitor_fs = CompetitorInfoFormSet(prefix='competitors')
        pharmacy_fs   = PharmacyReferenceFormSet(prefix='pharmacies')

    return render(request, 'crm/doctors/visit_form.html', {
        'form':          form,
        'product_fs':    product_fs,
        'investment_fs': investment_fs,
        'competitor_fs': competitor_fs,
        'pharmacy_fs':   pharmacy_fs,
        'action':        'Log New Visit',
    })


@crm_access_required
def visit_edit(request, pk):
    visit = get_object_or_404(DoctorVisit, pk=pk)

    if request.method == 'POST':
        form          = DoctorVisitForm(request.POST, instance=visit)
        product_fs    = VisitProductDetailFormSet(request.POST, instance=visit, prefix='products')
        investment_fs = DoctorInvestmentFormSet(request.POST, instance=visit, prefix='investments')
        competitor_fs = CompetitorInfoFormSet(request.POST, instance=visit, prefix='competitors')
        pharmacy_fs   = PharmacyReferenceFormSet(request.POST, instance=visit, prefix='pharmacies')

        if (form.is_valid() and product_fs.is_valid() and
                investment_fs.is_valid() and competitor_fs.is_valid() and
                pharmacy_fs.is_valid()):
            form.save()
            for fs in [product_fs, investment_fs, competitor_fs, pharmacy_fs]:
                fs.save()
            messages.success(request, 'Visit updated.')
            return redirect('crm_doctors:visit_detail', pk=pk)
    else:
        form          = DoctorVisitForm(instance=visit)
        product_fs    = VisitProductDetailFormSet(instance=visit, prefix='products')
        investment_fs = DoctorInvestmentFormSet(instance=visit, prefix='investments')
        competitor_fs = CompetitorInfoFormSet(instance=visit, prefix='competitors')
        pharmacy_fs   = PharmacyReferenceFormSet(instance=visit, prefix='pharmacies')

    return render(request, 'crm/doctors/visit_form.html', {
        'form':          form,
        'product_fs':    product_fs,
        'investment_fs': investment_fs,
        'competitor_fs': competitor_fs,
        'pharmacy_fs':   pharmacy_fs,
        'action':        'Edit Visit',
        'obj':           visit,
    })


@crm_access_required
def visit_delete(request, pk):
    obj = get_object_or_404(DoctorVisit, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Visit deleted.')
        return redirect('crm_doctors:visit_list')
    return render(request, 'crm/confirm_delete.html', {
        'obj': obj,
        'obj_name': f'Visit by {obj.mr.name} → Dr. {obj.doctor.doctor_name} ({obj.visit_date})'
    })


@crm_access_required
def doctor_locations_api(request, doctor_id):
    locations = DoctorPracticeLocation.objects.filter(
        doctor_id=doctor_id,
        is_active=True,
    ).order_by('location_name')

    return JsonResponse({
        'results': [
            {
                'id': loc.id,
                'name': loc.location_name,
                'type': loc.get_location_type_display(),
                'address': loc.address or '',
            }
            for loc in locations
        ]
    })


@crm_access_required
def doctor_last_visit_api(request, doctor_id):
    visit = (
        DoctorVisit.objects.select_related('mr', 'doctor', 'visit_location')
        .prefetch_related(
            'product_details__product',
            'investments',
            'competitor_info',
            'pharmacy_references',
        )
        .filter(doctor_id=doctor_id)
        .order_by('-visit_date', '-visit_time', '-id')
        .first()
    )

    if not visit:
        return JsonResponse({'found': False})

    return JsonResponse({
        'found': True,
        'visit': {
            'id': visit.id,
            'mr_name': visit.mr.name,
            'mr_id': visit.mr.mr_id,
            'doctor_name': visit.doctor.doctor_name,
            'doctor_specialty': visit.doctor.specialty,
            'visit_date': visit.visit_date.isoformat(),
            'visit_time': visit.visit_time.strftime('%H:%M'),
            'visit_status': visit.get_visit_type_display(),
            'visit_location': visit.visit_location.location_name if visit.visit_location else (visit.hospital_clinic_name or ''),
            'gps_address': visit.gps_address or '',
            'gps_latitude': str(visit.gps_latitude) if visit.gps_latitude is not None else '',
            'gps_longitude': str(visit.gps_longitude) if visit.gps_longitude is not None else '',
            'next_follow_up_date': visit.next_follow_up_date.isoformat() if visit.next_follow_up_date else '',
            'remarks': visit.remarks or '',
            'products': [
                {
                    'name': pd.product.product_name,
                    'strength': pd.product.strength,
                    'samples_given': pd.samples_given,
                    'units_day': pd.estimated_units_prescribed_per_day,
                    'units_month': pd.estimated_units_prescribed_per_month,
                    'value_month': str(pd.estimated_value_per_month),
                }
                for pd in visit.product_details.all()
            ],
            'investments': [
                {
                    'type': inv.get_investment_type_display(),
                    'amount': str(inv.amount),
                    'description': inv.description or '',
                }
                for inv in visit.investments.all()
            ],
            'competitors': [
                {
                    'product_name': ci.competitor_product_name,
                    'company': ci.competitor_company,
                    'notes': ci.notes or '',
                }
                for ci in visit.competitor_info.all()
            ],
            'pharmacies': [
                {
                    'store_name': ph.store_name,
                    'store_location': ph.store_location or '',
                }
                for ph in visit.pharmacy_references.all()
            ],
        }
    })

