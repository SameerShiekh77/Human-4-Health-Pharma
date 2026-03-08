

## ═══════════════════════════════════════════════════════════
## crm_analytics/views.py
## ═══════════════════════════════════════════════════════════

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import date, timedelta

from .models import (MRPerformanceSnapshot, DoctorPerformanceSnapshot,
                     DistributorPerformanceSnapshot, ProductPerformanceSnapshot,
                     ExpiryAlert)


@login_required
def dashboard(request):
    """
    Main CRM dashboard — aggregated KPIs and recent activity.
    """
    from crm_products.models import ProductMaster, BatchManagement, CompanyStock
    from crm_distributors.models import Distributor
    from crm_sales.models import MedicalRepresentative
    from crm_doctors.models import Doctor, DoctorVisit

    today = date.today()
    month_start = today.replace(day=1)

    # Core counts
    ctx = {
        'total_products':     ProductMaster.objects.filter(status='active').count(),
        'total_distributors': Distributor.objects.filter(status='active').count(),
        'total_mrs':          MedicalRepresentative.objects.filter(status='active').count(),
        'total_doctors':      Doctor.objects.filter(status='active').count(),

        # Today's visits
        'visits_today': DoctorVisit.objects.filter(visit_date=today).count(),
        'visits_month': DoctorVisit.objects.filter(visit_date__gte=month_start).count(),

        # GPS verified this month
        'gps_verified_month': DoctorVisit.objects.filter(
            visit_date__gte=month_start, is_gps_verified=True
        ).count(),

        # Expiry alerts
        'expiry_alerts_count': ExpiryAlert.objects.filter(is_acknowledged=False).count(),
        'near_expiry_batches': BatchManagement.objects.filter(batch_status='near_expiry').count(),
        'expired_batches':     BatchManagement.objects.filter(batch_status='expired').count(),

        # Low stock
        'low_stock_items': sum(
            1 for s in CompanyStock.objects.all() if s.is_low_stock
        ),

        # Recent visits
        'recent_visits': DoctorVisit.objects.select_related('mr', 'doctor')
                            .order_by('-visit_date', '-visit_time')[:8],

        # Top MRs this month (by visit count)
        'top_mrs': MRPerformanceSnapshot.objects.filter(
            snapshot_month=month_start
        ).order_by('-total_visits')[:5],

        # Unacknowledged alerts
        'pending_alerts': ExpiryAlert.objects.filter(
            is_acknowledged=False
        ).select_related('product').order_by('expiry_date')[:5],
    }
    return render(request, 'crm/analytics/dashboard.html', ctx)


@login_required
def mr_performance(request):
    qs = MRPerformanceSnapshot.objects.select_related('mr').order_by('-snapshot_month', '-total_visits')

    month = request.GET.get('month', '')
    mr_id = request.GET.get('mr', '')
    if month:
        qs = qs.filter(snapshot_month__startswith=month)
    if mr_id:
        qs = qs.filter(mr_id=mr_id)

    from crm_sales.models import MedicalRepresentative
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/analytics/mr_performance.html', {
        'page_obj': page,
        'mrs': MedicalRepresentative.objects.filter(status='active'),
        'total': qs.count(),
    })


@login_required
def doctor_performance(request):
    qs = DoctorPerformanceSnapshot.objects.select_related('doctor').order_by('-snapshot_month')

    month  = request.GET.get('month', '')
    doc_id = request.GET.get('doctor', '')
    if month:
        qs = qs.filter(snapshot_month__startswith=month)
    if doc_id:
        qs = qs.filter(doctor_id=doc_id)

    from crm_doctors.models import Doctor
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/analytics/doctor_performance.html', {
        'page_obj': page,
        'doctors': Doctor.objects.filter(status='active'),
        'total': qs.count(),
    })


@login_required
def distributor_performance(request):
    qs = DistributorPerformanceSnapshot.objects.select_related('distributor').order_by('-snapshot_month')

    month   = request.GET.get('month', '')
    dist_id = request.GET.get('distributor', '')
    if month:
        qs = qs.filter(snapshot_month__startswith=month)
    if dist_id:
        qs = qs.filter(distributor_id=dist_id)

    from crm_distributors.models import Distributor
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/analytics/distributor_performance.html', {
        'page_obj': page,
        'distributors': Distributor.objects.filter(status='active'),
        'total': qs.count(),
    })


@login_required
def product_performance(request):
    qs = ProductPerformanceSnapshot.objects.select_related(
        'product', 'region', 'distributor', 'mr'
    ).order_by('-snapshot_month', '-revenue')

    month    = request.GET.get('month', '')
    prod_id  = request.GET.get('product', '')
    if month:
        qs = qs.filter(snapshot_month__startswith=month)
    if prod_id:
        qs = qs.filter(product_id=prod_id)

    from crm_products.models import ProductMaster
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/analytics/product_performance.html', {
        'page_obj': page,
        'products': ProductMaster.objects.filter(status='active'),
        'total':    qs.count(),
    })


@login_required
def expiry_alerts(request):
    qs = ExpiryAlert.objects.select_related('product', 'distributor').order_by('expiry_date')

    ack_filter = request.GET.get('ack', '')
    alert_type = request.GET.get('type', '')
    source     = request.GET.get('source', '')

    if ack_filter == '0':
        qs = qs.filter(is_acknowledged=False)
    elif ack_filter == '1':
        qs = qs.filter(is_acknowledged=True)
    if alert_type:
        qs = qs.filter(alert_type=alert_type)
    if source:
        qs = qs.filter(source=source)

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/analytics/expiry_alerts.html', {
        'page_obj':    page,
        'total':       qs.count(),
        'pending':     ExpiryAlert.objects.filter(is_acknowledged=False).count(),
        'alert_types': ExpiryAlert.ALERT_TYPE_CHOICES,
        'sources':     ExpiryAlert.SOURCE_CHOICES,
    })


@login_required
def acknowledge_alert(request, pk):
    alert = get_object_or_404(ExpiryAlert, pk=pk)
    if request.method == 'POST':
        alert.acknowledge(request.user.get_full_name() or request.user.username)
        messages.success(request, f'Alert acknowledged for {alert.product.product_name}.')
    return redirect('crm_analytics:expiry_alerts')
