## ── crm_stores/views.py ─────────────────────────────────────

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from crm_stores.models import MedicalStore, StoreProductTracking
from crm_stores.forms import MedicalStoreForm, StoreProductTrackingForm


@login_required
def store_list(request):
    qs = MedicalStore.objects.select_related('area', 'distributor')
    q      = request.GET.get('q', '')
    status = request.GET.get('status', '')
    area   = request.GET.get('area', '')

    if q:
        qs = qs.filter(Q(store_name__icontains=q) | Q(owner_name__icontains=q) | Q(store_id__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if area:
        qs = qs.filter(area_id=area)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    from crm_sales.models import Area
    return render(request, 'crm/stores/store_list.html', {
        'page_obj': page,
        'query':    q,
        'areas':    Area.objects.filter(is_active=True),
        'total':    qs.count(),
    })


@login_required
def store_detail(request, pk):
    store    = get_object_or_404(MedicalStore, pk=pk)
    products = store.product_trackings.select_related('product')
    return render(request, 'crm/stores/store_detail.html', {
        'store': store,
        'products': products,
    })


@login_required
def store_create(request):
    form = MedicalStoreForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Medical store added.')
        return redirect('crm_stores:store_list')
    return render(request, 'crm/stores/store_form.html', {'form': form, 'action': 'Add'})


@login_required
def store_edit(request, pk):
    obj  = get_object_or_404(MedicalStore, pk=pk)
    form = MedicalStoreForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Store updated.')
        return redirect('crm_stores:store_detail', pk=pk)
    return render(request, 'crm/stores/store_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def store_delete(request, pk):
    obj = get_object_or_404(MedicalStore, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Store deleted.')
        return redirect('crm_stores:store_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': obj.store_name})


@login_required
def store_product_tracking_create(request, store_pk):
    store = get_object_or_404(MedicalStore, pk=store_pk)
    form  = StoreProductTrackingForm(request.POST or None, initial={'store': store})
    if request.method == 'POST' and form.is_valid():
        tracking = form.save(commit=False)
        tracking.store = store
        tracking.last_updated_by_mr = request.user.get_full_name() or request.user.username
        tracking.save()
        messages.success(request, 'Product tracking added.')
        return redirect('crm_stores:store_detail', pk=store_pk)
    return render(request, 'crm/stores/store_product_form.html', {'form': form, 'store': store})
