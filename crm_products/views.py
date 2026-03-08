from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import Division, ProductMaster, BatchManagement, CompanyStock
from .forms import DivisionForm, ProductMasterForm, BatchManagementForm, CompanyStockForm


# ─────────────────────────────────────────
# DIVISION VIEWS
# ─────────────────────────────────────────

@login_required
def division_list(request):
    qs = Division.objects.annotate(product_count=Count('products'))
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(manager_name__icontains=q))

    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/products/division_list.html', {
        'page_obj': page,
        'query': q,
        'total': qs.count(),
    })


@login_required
def division_create(request):
    form = DivisionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Division created successfully.')
        return redirect('crm_products:division_list')
    return render(request, 'crm/products/division_form.html', {'form': form, 'action': 'Create'})


@login_required
def division_edit(request, pk):
    obj = get_object_or_404(Division, pk=pk)
    form = DivisionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Division updated.')
        return redirect('crm_products:division_list')
    return render(request, 'crm/products/division_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def division_delete(request, pk):
    obj = get_object_or_404(Division, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Division deleted.')
        return redirect('crm_products:division_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': obj.name})


# ─────────────────────────────────────────
# PRODUCT VIEWS
# ─────────────────────────────────────────

@login_required
def product_list(request):
    qs = ProductMaster.objects.select_related('division')

    q       = request.GET.get('q', '')
    cat     = request.GET.get('category', '')
    status  = request.GET.get('status', '')
    div     = request.GET.get('division', '')

    if q:
        qs = qs.filter(
            Q(product_name__icontains=q) |
            Q(generic_name__icontains=q) |
            Q(brand_name__icontains=q) |
            Q(product_id__icontains=q)
        )
    if cat:
        qs = qs.filter(category=cat)
    if status:
        qs = qs.filter(status=status)
    if div:
        qs = qs.filter(division_id=div)

    paginator = Paginator(qs, 20)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/products/product_list.html', {
        'page_obj':   page,
        'query':      q,
        'divisions':  Division.objects.filter(is_active=True),
        'categories': ProductMaster.CATEGORY_CHOICES,
        'total':      qs.count(),
        'active_count':   ProductMaster.objects.filter(status='active').count(),
        'inactive_count': ProductMaster.objects.filter(status='inactive').count(),
    })


@login_required
def product_detail(request, pk):
    product = get_object_or_404(ProductMaster, pk=pk)
    batches = product.batches.order_by('expiry_date')
    return render(request, 'crm/products/product_detail.html', {
        'product': product,
        'batches': batches,
        'active_batches': batches.filter(batch_status='active').count(),
        'near_expiry_batches': batches.filter(batch_status='near_expiry').count(),
        'expired_batches': batches.filter(batch_status='expired').count(),
    })


@login_required
def product_create(request):
    form = ProductMasterForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product created successfully.')
        return redirect('crm_products:product_list')
    return render(request, 'crm/products/product_form.html', {'form': form, 'action': 'Add New'})


@login_required
def product_edit(request, pk):
    obj  = get_object_or_404(ProductMaster, pk=pk)
    form = ProductMasterForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product updated.')
        return redirect('crm_products:product_detail', pk=pk)
    return render(request, 'crm/products/product_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def product_delete(request, pk):
    obj = get_object_or_404(ProductMaster, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Product deleted.')
        return redirect('crm_products:product_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': obj.product_name})


# ─────────────────────────────────────────
# BATCH VIEWS
# ─────────────────────────────────────────

@login_required
def batch_list(request):
    qs = BatchManagement.objects.select_related('product')

    q       = request.GET.get('q', '')
    status  = request.GET.get('status', '')
    product = request.GET.get('product', '')

    if q:
        qs = qs.filter(
            Q(batch_number__icontains=q) |
            Q(product__product_name__icontains=q)
        )
    if status:
        qs = qs.filter(batch_status=status)
    if product:
        qs = qs.filter(product_id=product)

    # Update batch statuses before display
    today = timezone.now().date()
    for batch in qs:
        batch.save()  # triggers auto status update

    paginator = Paginator(qs.order_by('expiry_date'), 20)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/products/batch_list.html', {
        'page_obj':    page,
        'query':       q,
        'products':    ProductMaster.objects.filter(status='active'),
        'total':       qs.count(),
        'active':      qs.filter(batch_status='active').count(),
        'near_expiry': qs.filter(batch_status='near_expiry').count(),
        'expired':     qs.filter(batch_status='expired').count(),
    })


@login_required
def batch_detail(request, pk):
    batch = get_object_or_404(BatchManagement, pk=pk)
    return render(request, 'crm/products/batch_detail.html', {'batch': batch})


@login_required
def batch_create(request):
    form = BatchManagementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Batch added successfully.')
        return redirect('crm_products:batch_list')
    return render(request, 'crm/products/batch_form.html', {'form': form, 'action': 'Create'})


@login_required
def batch_edit(request, pk):
    obj  = get_object_or_404(BatchManagement, pk=pk)
    form = BatchManagementForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Batch updated.')
        return redirect('crm_products:batch_detail', pk=pk)
    return render(request, 'crm/products/batch_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def batch_delete(request, pk):
    obj = get_object_or_404(BatchManagement, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Batch deleted.')
        return redirect('crm_products:batch_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': obj.batch_number})


# ─────────────────────────────────────────
# COMPANY STOCK VIEWS
# ─────────────────────────────────────────

@login_required
def stock_list(request):
    qs = CompanyStock.objects.select_related('product', 'batch')

    q       = request.GET.get('q', '')
    loc     = request.GET.get('location', '')
    alert   = request.GET.get('alert', '')

    if q:
        qs = qs.filter(
            Q(product__product_name__icontains=q) |
            Q(batch__batch_number__icontains=q)
        )
    if loc:
        qs = qs.filter(warehouse_location=loc)

    paginator = Paginator(qs, 20)
    page      = paginator.get_page(request.GET.get('page'))

    # Filter by alert AFTER pagination fetch (using properties)
    all_stock  = list(qs)
    low_count  = sum(1 for s in all_stock if s.is_low_stock)
    exp_count  = sum(1 for s in all_stock if s.is_near_expiry)

    return render(request, 'crm/products/stock_list.html', {
        'page_obj':  page,
        'query':     q,
        'total':     qs.count(),
        'low_count': low_count,
        'exp_count': exp_count,
        'locations': CompanyStock.WAREHOUSE_CHOICES,
    })


@login_required
def stock_create(request):
    form = CompanyStockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Stock record created.')
        return redirect('crm_products:stock_list')
    return render(request, 'crm/products/stock_form.html', {'form': form, 'action': 'Add'})


@login_required
def stock_edit(request, pk):
    obj  = get_object_or_404(CompanyStock, pk=pk)
    form = CompanyStockForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Stock record updated.')
        return redirect('crm_products:stock_list')
    return render(request, 'crm/products/stock_form.html', {'form': form, 'action': 'Edit', 'obj': obj})


@login_required
def stock_delete(request, pk):
    obj = get_object_or_404(CompanyStock, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Stock record deleted.')
        return redirect('crm_products:stock_list')
    return render(request, 'crm/confirm_delete.html', {'obj': obj, 'obj_name': f'{obj.product.product_name} / {obj.batch.batch_number}'})