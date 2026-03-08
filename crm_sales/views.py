## ── crm_sales/views.py ──────────────────────────────────────

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.models import User

from .models import Region, Area, MedicalRepresentative
from crm_products.models import Division
from .forms import RegionForm, AreaForm, MedicalRepresentativeForm


# ─── REGION ──────────────────────────────

@login_required
def region_list(request):
    qs = Region.objects.select_related('division').annotate(area_count=Count('areas'))
    q = request.GET.get('q', '')
    div = request.GET.get('division', '')
    if q:
        qs = qs.filter(Q(region_name__icontains=q) | Q(regional_manager__icontains=q))
    if div:
        qs = qs.filter(division_id=div)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'crm/sales/region_list.html', {
        'page_obj': page,
        'query': q,
        'divisions': Division.objects.filter(is_active=True),
        'total': qs.count(),
    })


@login_required
def region_create(request):
    form = RegionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Region created.')
        return redirect('crm_sales:region_list')
    return render(request, 'crm/sales/region_form.html', {'form': form, 'action': 'Create'})


@login_required
def region_edit(request, pk):
    obj = get_object_or_404(Region, pk=pk)
    form = RegionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Region updated.')
        return redirect('crm_sales:region_list')
    return render(request, 'crm/sales/region_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def region_delete(request, pk):
    obj = get_object_or_404(Region, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Region deleted.')
        return redirect('crm_sales:region_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': obj.region_name})


# ─── AREA ────────────────────────────────

@login_required
def area_list(request):
    qs = Area.objects.select_related('region', 'region__division').annotate(mr_count=Count('mrs'))
    q = request.GET.get('q', '')
    region = request.GET.get('region', '')
    if q:
        qs = qs.filter(Q(area_name__icontains=q) | Q(area_manager__icontains=q))
    if region:
        qs = qs.filter(region_id=region)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'crm/sales/area_list.html', {
        'page_obj': page,
        'query': q,
        'regions': Region.objects.filter(is_active=True),
        'total': qs.count(),
    })


@login_required
def area_create(request):
    form = AreaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Area created.')
        return redirect('crm_sales:area_list')
    return render(request, 'crm/sales/area_form.html', {'form': form, 'action': 'Create'})


@login_required
def area_edit(request, pk):
    obj = get_object_or_404(Area, pk=pk)
    form = AreaForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Area updated.')
        return redirect('crm_sales:area_list')
    return render(request, 'crm/sales/area_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def area_delete(request, pk):
    obj = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Area deleted.')
        return redirect('crm_sales:area_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': obj.area_name})


# ─── MEDICAL REPRESENTATIVE ──────────────

@login_required
def mr_list(request):
    qs = MedicalRepresentative.objects.select_related('division', 'region', 'area')
    q      = request.GET.get('q', '')
    status = request.GET.get('status', '')
    region = request.GET.get('region', '')

    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(mr_id__icontains=q) |
            Q(phone_number__icontains=q) | Q(cnic__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if region:
        qs = qs.filter(region_id=region)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/sales/mr_list.html', {
        'page_obj': page,
        'query':    q,
        'regions':  Region.objects.filter(is_active=True),
        'total':    qs.count(),
        'active':   MedicalRepresentative.objects.filter(status='active').count(),
    })


@login_required
def mr_detail(request, pk):
    mr = get_object_or_404(MedicalRepresentative, pk=pk)
    visits  = mr.doctor_visits.select_related('doctor').order_by('-visit_date')[:10]
    doctors = mr.assigned_doctors.all()
    return render(request, 'crm/sales/mr_detail.html', {
        'mr': mr,
        'recent_visits': visits,
        'assigned_doctors': doctors,
        'total_visits': mr.doctor_visits.count(),
        'gps_visits':   mr.doctor_visits.filter(is_gps_verified=True).count(),
    })


@login_required
def mr_create(request):
    form = MedicalRepresentativeForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Medical Representative added.')
        return redirect('crm_sales:mr_list')
    return render(request, 'crm/sales/mr_form.html', {'form': form, 'action': 'Add'})


@login_required
def mr_edit(request, pk):
    obj  = get_object_or_404(MedicalRepresentative, pk=pk)
    form = MedicalRepresentativeForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'MR profile updated.')
        return redirect('crm_sales:mr_detail', pk=pk)
    return render(request, 'crm/sales/mr_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def mr_delete(request, pk):
    obj = get_object_or_404(MedicalRepresentative, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'MR deleted.')
        return redirect('crm_sales:mr_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': obj.name})
