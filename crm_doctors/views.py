## ── crm_doctors/views.py ────────────────────────────────────

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.forms import inlineformset_factory

from .models import (Doctor, DoctorVisit, VisitProductDetail,
                     CompetitorInfo, DoctorInvestment, PharmacyReference)
from .forms import (DoctorForm, DoctorVisitForm,
                    VisitProductDetailFormSet, DoctorInvestmentFormSet,
                    CompetitorInfoFormSet, PharmacyReferenceFormSet)


# ─── DOCTOR ──────────────────────────────

@login_required
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
    })


@login_required
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


@login_required
def doctor_create(request):
    form = DoctorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Doctor profile created.')
        return redirect('crm_doctors:doctor_list')
    return render(request, 'crm/doctors/doctor_form.html', {'form': form, 'action': 'Add'})


@login_required
def doctor_edit(request, pk):
    obj  = get_object_or_404(Doctor, pk=pk)
    form = DoctorForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Doctor profile updated.')
        return redirect('crm_doctors:doctor_detail', pk=pk)
    return render(request, 'crm/doctors/doctor_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def doctor_delete(request, pk):
    obj = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Doctor deleted.')
        return redirect('crm_doctors:doctor_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': f'Dr. {obj.doctor_name}'})


# ─── DOCTOR VISIT (MOST IMPORTANT) ───────

@login_required
def visit_list(request):
    qs = DoctorVisit.objects.select_related('mr', 'doctor').order_by('-visit_date', '-visit_time')

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
    })


@login_required
def visit_detail(request, pk):
    visit = get_object_or_404(
        DoctorVisit.objects.select_related('mr', 'doctor')
            .prefetch_related('product_details__product',
                              'investments',
                              'competitor_info',
                              'pharmacy_references'),
        pk=pk
    )
    return render(request, 'crm/doctors/visit_detail.html', {'visit': visit})


@login_required
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


@login_required
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


@login_required
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

