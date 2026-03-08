## ── crm_distributors/views.py ──────────────────────────────

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count

from .models import Distributor, DistributorStockEntry, DistributorSalesValue
from .forms import DistributorForm, DistributorStockEntryForm, DistributorSalesValueForm


# ─── DISTRIBUTOR ────────────────────────

@login_required
def distributor_list(request):
    qs = Distributor.objects.all()
    q      = request.GET.get('q', '')
    status = request.GET.get('status', '')
    city   = request.GET.get('city', '')

    if q:
        qs = qs.filter(
            Q(distributor_name__icontains=q) |
            Q(owner_name__icontains=q) |
            Q(distributor_id__icontains=q) |
            Q(license_number__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if city:
        qs = qs.filter(city__icontains=city)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    cities = Distributor.objects.values_list('city', flat=True).distinct().order_by('city')

    return render(request, 'crm/distributors/distributor_list.html', {
        'page_obj': page,
        'query': q,
        'cities': cities,
        'total': qs.count(),
        'active': Distributor.objects.filter(status='active').count(),
    })


@login_required
def distributor_detail(request, pk):
    dist = get_object_or_404(Distributor, pk=pk)
    entries = dist.stock_entries.select_related('product').order_by('-date_submitted')[:10]
    sales   = dist.sales_values.select_related('product').order_by('-sale_date')[:10]
    total_sales = sum(s.total_sales_value for s in dist.sales_values.all())
    return render(request, 'crm/distributors/distributor_detail.html', {
        'dist': dist,
        'entries': entries,
        'sales': sales,
        'total_sales': total_sales,
    })


@login_required
def distributor_create(request):
    form = DistributorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Distributor added successfully.')
        return redirect('crm_distributors:distributor_list')
    return render(request, 'crm/distributors/distributor_form.html', {'form': form, 'action': 'Add'})


@login_required
def distributor_edit(request, pk):
    obj  = get_object_or_404(Distributor, pk=pk)
    form = DistributorForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Distributor updated.')
        return redirect('crm_distributors:distributor_detail', pk=pk)
    return render(request, 'crm/distributors/distributor_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def distributor_delete(request, pk):
    obj = get_object_or_404(Distributor, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Distributor deleted.')
        return redirect('crm_distributors:distributor_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': obj.distributor_name})


# ─── STOCK ENTRY ─────────────────────────

@login_required
def stock_entry_list(request):
    qs = DistributorStockEntry.objects.select_related('distributor', 'product')

    q    = request.GET.get('q', '')
    dist = request.GET.get('distributor', '')

    if q:
        qs = qs.filter(
            Q(distributor__distributor_name__icontains=q) |
            Q(product__product_name__icontains=q)
        )
    if dist:
        qs = qs.filter(distributor_id=dist)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/distributors/stock_entry_list.html', {
        'page_obj':     page,
        'query':        q,
        'distributors': Distributor.objects.filter(status='active'),
        'total':        qs.count(),
    })


@login_required
def stock_entry_detail(request, pk):
    entry = get_object_or_404(DistributorStockEntry, pk=pk)
    return render(request, 'crm/distributors/stock_entry_detail.html', {'entry': entry})


@login_required
def stock_entry_create(request):
    form = DistributorStockEntryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Stock entry submitted.')
        return redirect('crm_distributors:stock_entry_list')
    return render(request, 'crm/distributors/stock_entry_form.html', {'form': form, 'action': 'Submit'})


@login_required
def stock_entry_edit(request, pk):
    obj  = get_object_or_404(DistributorStockEntry, pk=pk)
    form = DistributorStockEntryForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Stock entry updated.')
        return redirect('crm_distributors:stock_entry_detail', pk=pk)
    return render(request, 'crm/distributors/stock_entry_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def stock_entry_delete(request, pk):
    obj = get_object_or_404(DistributorStockEntry, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Entry deleted.')
        return redirect('crm_distributors:stock_entry_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': f'{obj.distributor} / {obj.product}'})


# ─── SALES VALUE ──────────────────────────

@login_required
def sales_value_list(request):
    qs = DistributorSalesValue.objects.select_related('distributor', 'product')
    dist = request.GET.get('distributor', '')
    if dist:
        qs = qs.filter(distributor_id=dist)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    total_value = sum(s.total_sales_value for s in qs)

    return render(request, 'crm/distributors/sales_value_list.html', {
        'page_obj':     page,
        'distributors': Distributor.objects.filter(status='active'),
        'total_value':  total_value,
    })


@login_required
def sales_value_create(request):
    form = DistributorSalesValueForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sales value recorded.')
        return redirect('crm_distributors:sales_value_list')
    return render(request, 'crm/distributors/sales_value_form.html', {'form': form, 'action': 'Add'})


@login_required
def sales_value_delete(request, pk):
    obj = get_object_or_404(DistributorSalesValue, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Record deleted.')
        return redirect('crm_distributors:sales_value_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': str(obj)})