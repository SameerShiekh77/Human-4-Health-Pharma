

## ═══════════════════════════════════════════════════════════
## crm_analytics/views.py
## ═══════════════════════════════════════════════════════════

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group, Permission
from django.contrib import messages
from core.auth_utils import (
    CRM_ROLE_PREFIX,
    crm_access_required,
    is_crm_user,
    get_crm_permission_groups,
    get_crm_allowed_permission_ids,
)
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg, F, Max
from django.utils import timezone
from datetime import date

from .models import (MRPerformanceSnapshot, DoctorPerformanceSnapshot,
                     DistributorPerformanceSnapshot, ProductPerformanceSnapshot,
                     ExpiryAlert)


def _get_month_bounds(month_value):
    start = date.fromisoformat(f'{month_value}-01')
    if start.month == 12:
        next_start = date(start.year + 1, 1, 1)
    else:
        next_start = date(start.year, start.month + 1, 1)
    return start, next_start


def _format_period_label(scope, month_value):
    if scope == 'all':
        return 'All Data'
    try:
        start = date.fromisoformat(f'{month_value}-01')
    except ValueError:
        return 'Current Month'
    return start.strftime('%B %Y')


def _safe_percentage(numerator, denominator):
    if not denominator:
        return 0
    return round((numerator / denominator) * 100, 1)


def _attach_mr_metrics(rows):
    for row in rows:
        total_visits = row.get('total_visits') or 0
        gps_verified = row.get('gps_verified_visits') or 0
        total_value = row.get('total_prescription_value_generated') or 0
        total_investment = row.get('total_investment_given') or 0
        row['gps_verified_percentage'] = _safe_percentage(gps_verified, total_visits)
        row['roi'] = total_value - total_investment
        row['efficiency_score'] = round(float(row.get('efficiency_score') or 0), 1)
    return rows


def _attach_doctor_metrics(rows):
    for row in rows:
        visits = row.get('total_visits_received') or 0
        value = row.get('estimated_prescription_per_month') or 0
        investment = row.get('total_investment_given') or 0
        row['roi'] = value - investment
        row['visit_rate'] = visits
    return rows


def _attach_distributor_metrics(rows):
    for row in rows:
        sold = row.get('total_units_sold') or 0
        unsold = row.get('total_unsold_stock') or 0
        expired = row.get('total_expired_stock') or 0
        total_stock = sold + unsold + expired
        row['efficiency_percentage'] = round(((sold / total_stock) * 100), 1) if total_stock else 0
    return rows


@crm_access_required
def dashboard(request):
    """
    Main CRM dashboard — aggregated KPIs and recent activity.
    """
    from django.contrib.auth.models import User
    from core.models import Contact, News, Teams, Cities, Subscribers
    from hr.models import Employee, Department
    from crm_products.models import ProductMaster, BatchManagement, CompanyStock
    from crm_distributors.models import Distributor
    from crm_sales.models import MedicalRepresentative, Region, Area
    from crm_doctors.models import Doctor, DoctorVisit

    today = timezone.localdate()
    scope = request.GET.get('scope', 'month')
    month_value = request.GET.get('month', today.strftime('%Y-%m'))

    if scope == 'all':
        period_start = None
        period_end = None
        period_label = 'All Data'
        previous_start = None
        previous_end = None
    else:
        try:
            period_start, period_end = _get_month_bounds(month_value)
        except ValueError:
            month_value = today.strftime('%Y-%m')
            period_start, period_end = _get_month_bounds(month_value)
        period_label = _format_period_label(scope, month_value)
        if period_start.month == 1:
            previous_start = date(period_start.year - 1, 12, 1)
        else:
            previous_start = date(period_start.year, period_start.month - 1, 1)
        previous_end = period_start

    visit_qs = DoctorVisit.objects.select_related('mr', 'doctor', 'visit_location').prefetch_related('product_details', 'investments')
    mr_snapshot_qs = MRPerformanceSnapshot.objects.select_related('mr')
    doctor_snapshot_qs = DoctorPerformanceSnapshot.objects.select_related('doctor')
    distributor_snapshot_qs = DistributorPerformanceSnapshot.objects.select_related('distributor')
    product_snapshot_qs = ProductPerformanceSnapshot.objects.select_related('product', 'region', 'distributor', 'mr')

    if scope != 'all':
        visit_qs = visit_qs.filter(visit_date__gte=period_start, visit_date__lt=period_end)
        mr_snapshot_qs = mr_snapshot_qs.filter(snapshot_month=period_start)
        doctor_snapshot_qs = doctor_snapshot_qs.filter(snapshot_month=period_start)
        distributor_snapshot_qs = distributor_snapshot_qs.filter(snapshot_month=period_start)
        product_snapshot_qs = product_snapshot_qs.filter(snapshot_month=period_start)

    period_visit_count = visit_qs.count()
    period_gps_verified = visit_qs.filter(is_gps_verified=True).count()
    period_doctors_covered = visit_qs.values('doctor_id').distinct().count()
    period_mrs_active = visit_qs.values('mr_id').distinct().count()

    previous_visit_count = 0
    previous_gps_verified = 0
    if scope != 'all':
        previous_visit_count = DoctorVisit.objects.filter(
            visit_date__gte=previous_start,
            visit_date__lt=previous_end,
        ).count()
        previous_gps_verified = DoctorVisit.objects.filter(
            visit_date__gte=previous_start,
            visit_date__lt=previous_end,
            is_gps_verified=True,
        ).count()

    mr_rows = list(mr_snapshot_qs.values('mr').annotate(
        mr_name=F('mr__name'),
        mr_code=F('mr__mr_id'),
        total_visits=Sum('total_visits'),
        gps_verified_visits=Sum('gps_verified_visits'),
        total_doctors_covered=Sum('total_doctors_covered'),
        total_prescription_value_generated=Sum('total_prescription_value_generated'),
        total_investment_given=Sum('total_investment_given'),
        efficiency_score=Avg('working_efficiency_score'),
        latest_month=Max('snapshot_month'),
    ).order_by('-total_visits', '-latest_month')[:5])
    mr_rows = _attach_mr_metrics(mr_rows)

    doctor_rows = list(doctor_snapshot_qs.values('doctor').annotate(
        doctor_name=F('doctor__doctor_name'),
        doctor_code=F('doctor__doctor_id'),
        specialty=F('doctor__specialty'),
        city=F('doctor__city'),
        total_visits_received=Sum('total_visits_received'),
        estimated_prescription_per_month=Sum('estimated_prescription_per_month'),
        total_investment_given=Sum('total_investment_given'),
        latest_month=Max('snapshot_month'),
    ).order_by('-total_visits_received', '-latest_month')[:5])
    doctor_rows = _attach_doctor_metrics(doctor_rows)

    distributor_rows = list(distributor_snapshot_qs.values('distributor').annotate(
        distributor_name=F('distributor__distributor_name'),
        city=F('distributor__city'),
        total_sales_value=Sum('total_sales_value'),
        total_units_sold=Sum('total_units_sold'),
        total_unsold_stock=Sum('total_unsold_stock'),
        total_expired_stock=Sum('total_expired_stock'),
        efficiency_percentage=Avg('efficiency_percentage'),
        latest_month=Max('snapshot_month'),
    ).order_by('-total_sales_value', '-latest_month')[:5])
    distributor_rows = _attach_distributor_metrics(distributor_rows)

    product_rows = list(product_snapshot_qs.values('product').annotate(
        product_name=F('product__product_name'),
        strength=F('product__strength'),
        category=F('product__category'),
        total_units_sold=Sum('units_sold'),
        total_revenue=Sum('revenue'),
        growth_percentage=Avg('growth_percentage'),
        latest_month=Max('snapshot_month'),
    ).order_by('-total_revenue', '-latest_month')[:5])
    for row in product_rows:
        row['growth_percentage'] = round(float(row.get('growth_percentage') or 0), 1)

    # Core counts
    ctx = {
        'period_label': period_label,
        'scope': scope,
        'month_value': month_value,
        'total_products': ProductMaster.objects.filter(status='active').count(),
        'total_distributors': Distributor.objects.filter(status='active').count(),
        'total_mrs': MedicalRepresentative.objects.filter(status='active').count(),
        'total_doctors': Doctor.objects.filter(status='active').count(),
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'total_departments': Department.objects.filter(is_active=True).count(),
        'total_regions': Region.objects.filter(is_active=True).count(),
        'total_areas': Area.objects.filter(is_active=True).count(),
        'total_news': News.objects.filter(is_published=True).count(),
        'total_teams': Teams.objects.filter(is_active=True).count(),
        'total_cities': Cities.objects.count(),
        'total_subscribers': Subscribers.objects.count(),
        'total_users': User.objects.count(),
        'unread_contacts': Contact.objects.filter(is_read=False).count(),

        # Today's visits
        'visits_today': DoctorVisit.objects.filter(visit_date=today).count(),
        'visits_month': DoctorVisit.objects.filter(
            visit_date__gte=today.replace(day=1)
        ).count(),
        'period_visit_count': period_visit_count,
        'period_gps_verified': period_gps_verified,
        'period_doctors_covered': period_doctors_covered,
        'period_mrs_active': period_mrs_active,
        'previous_visit_count': previous_visit_count,
        'previous_gps_verified': previous_gps_verified,

        # GPS verified this month
        'gps_verified_month': DoctorVisit.objects.filter(
            visit_date__gte=today.replace(day=1), is_gps_verified=True
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
        'recent_visits': visit_qs.order_by('-visit_date', '-visit_time')[:8],

        # Top MRs this month (by visit count)
        'top_mrs': mr_rows,
        'top_doctors': doctor_rows,
        'top_distributors': distributor_rows,
        'top_products': product_rows,

        # Unacknowledged alerts
        'pending_alerts': ExpiryAlert.objects.filter(
            is_acknowledged=False
        ).select_related('product').order_by('expiry_date')[:5],
        'recent_news': News.objects.filter(is_published=True).select_related('category', 'author').order_by('-created_at')[:5],
        'recent_contacts': Contact.objects.all().order_by('-created_at')[:5],
        'low_stock_products': CompanyStock.objects.select_related('product', 'batch').annotate(
            available_stock=F('batch__quantity_manufactured') - F('batch__quantity_sent_to_distributors')
        ).filter(available_stock__lte=F('low_stock_threshold')).order_by('available_stock')[:5],
        'month_select_value': month_value,
    }
    return render(request, 'crm/analytics/dashboard.html', ctx)


@crm_access_required
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


@crm_access_required
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


@crm_access_required
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


@crm_access_required
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


@crm_access_required
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


@crm_access_required
def acknowledge_alert(request, pk):
    alert = get_object_or_404(ExpiryAlert, pk=pk)
    if request.method == 'POST':
        alert.acknowledge(request.user.get_full_name() or request.user.username)
        messages.success(request, f'Alert acknowledged for {alert.product.product_name}.')
    return redirect('crm_analytics:expiry_alerts')


def crm_login(request):
    if request.user.is_authenticated:
        if is_crm_user(request.user):
            return redirect('crm_analytics:dashboard')
        if request.user.is_staff:
            return redirect('dashboard')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username=username, password=password)
        if user is None or not is_crm_user(user):
            messages.error(request, 'Invalid CRM credentials or insufficient CRM access.')
            return render(request, 'crm/login.html', {'username': username})

        login(request, user)
        if not remember_me:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(1209600)

        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
        return redirect('crm_analytics:dashboard')

    return render(request, 'crm/login.html')


def crm_logout(request):
    logout(request)
    messages.success(request, 'You have been signed out of CRM.')
    return redirect('crm_analytics:crm_login')


@crm_access_required
def crm_user_list(request):
    users = User.objects.filter(
        Q(groups__name__istartswith=CRM_ROLE_PREFIX) | Q(is_superuser=True)
    ).distinct().order_by('-date_joined')
    return render(request, 'crm/users/user_list.html', {'users': users})


@crm_access_required
def crm_user_create(request):
    roles = Group.objects.filter(name__istartswith=CRM_ROLE_PREFIX).order_by('name')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        role_id = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            role = get_object_or_404(Group, pk=role_id, name__istartswith=CRM_ROLE_PREFIX) if role_id else None
            if role is None:
                messages.error(request, 'Please select a CRM role.')
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                user.is_active = is_active
                user.is_staff = False
                user.save()
                user.groups.set([role])
                messages.success(request, 'CRM user created successfully.')
                return redirect('crm_analytics:crm_user_list')

    return render(request, 'crm/users/user_form.html', {
        'roles': roles,
        'action': 'Create',
    })


@crm_access_required
def crm_user_edit(request, id):
    user_obj = get_object_or_404(User, id=id)
    roles = Group.objects.filter(name__istartswith=CRM_ROLE_PREFIX).order_by('name')
    selected_role = user_obj.groups.filter(name__istartswith=CRM_ROLE_PREFIX).first()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        role_id = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'

        if User.objects.exclude(pk=user_obj.pk).filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            role = get_object_or_404(Group, pk=role_id, name__istartswith=CRM_ROLE_PREFIX) if role_id else None
            if role is None:
                messages.error(request, 'Please select a CRM role.')
            else:
                user_obj.username = username
                user_obj.email = email
                user_obj.first_name = first_name
                user_obj.last_name = last_name
                user_obj.is_active = is_active
                user_obj.is_staff = False
                if password:
                    user_obj.set_password(password)
                user_obj.save()
                user_obj.groups.set([role])
                messages.success(request, 'CRM user updated successfully.')
                return redirect('crm_analytics:crm_user_list')

    return render(request, 'crm/users/user_form.html', {
        'user_obj': user_obj,
        'roles': roles,
        'selected_role': selected_role,
        'action': 'Edit',
    })


@crm_access_required
def crm_user_delete(request, id):
    user_obj = get_object_or_404(User, id=id)
    if request.method == 'POST':
        if user_obj == request.user:
            messages.error(request, 'You cannot delete your own CRM account.')
        else:
            user_obj.delete()
            messages.success(request, 'CRM user deleted successfully.')
    return redirect('crm_analytics:crm_user_list')


@crm_access_required
def crm_role_list(request):
    roles = Group.objects.filter(name__istartswith=CRM_ROLE_PREFIX).annotate(
        user_count=Count('user'),
        permission_count=Count('permissions', distinct=True),
    ).order_by('name')
    return render(request, 'crm/users/role_list.html', {'roles': roles})


@crm_access_required
def crm_role_create(request):
    permission_groups = get_crm_permission_groups()
    allowed_permission_ids = get_crm_allowed_permission_ids()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        selected_permission_ids = {
            int(pid) for pid in request.POST.getlist('permissions') if pid.isdigit()
        }
        selected_permission_ids &= allowed_permission_ids

        if not name:
            messages.error(request, 'Role name is required.')
        else:
            role_name = name if name.upper().startswith(CRM_ROLE_PREFIX.upper()) else f'{CRM_ROLE_PREFIX}{name}'
            if Group.objects.filter(name=role_name).exists():
                messages.error(request, 'Role already exists.')
            else:
                role = Group.objects.create(name=role_name)
                if selected_permission_ids:
                    permissions = Permission.objects.filter(id__in=selected_permission_ids)
                    role.permissions.set(permissions)
                messages.success(request, 'CRM role created successfully.')
                return redirect('crm_analytics:crm_role_list')
    return render(request, 'crm/users/role_form.html', {
        'action': 'Create',
        'permission_groups': permission_groups,
        'selected_permission_ids': set(),
    })


@crm_access_required
def crm_role_edit(request, id):
    role = get_object_or_404(Group, id=id, name__istartswith=CRM_ROLE_PREFIX)
    permission_groups = get_crm_permission_groups()
    allowed_permission_ids = get_crm_allowed_permission_ids()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        selected_permission_ids = {
            int(pid) for pid in request.POST.getlist('permissions') if pid.isdigit()
        }
        selected_permission_ids &= allowed_permission_ids

        if not name:
            messages.error(request, 'Role name is required.')
        else:
            role_name = name if name.upper().startswith(CRM_ROLE_PREFIX.upper()) else f'{CRM_ROLE_PREFIX}{name}'
            if Group.objects.exclude(pk=role.pk).filter(name=role_name).exists():
                messages.error(request, 'Role already exists.')
            else:
                role.name = role_name
                role.save()
                permissions = Permission.objects.filter(id__in=selected_permission_ids)
                role.permissions.set(permissions)
                messages.success(request, 'CRM role updated successfully.')
                return redirect('crm_analytics:crm_role_list')

    selected_permission_ids = set(role.permissions.values_list('id', flat=True))
    return render(request, 'crm/users/role_form.html', {
        'role': role,
        'action': 'Edit',
        'permission_groups': permission_groups,
        'selected_permission_ids': selected_permission_ids,
    })


@crm_access_required
def crm_role_delete(request, id):
    role = get_object_or_404(Group, id=id, name__istartswith=CRM_ROLE_PREFIX)
    if request.method == 'POST':
        if role.user_set.exists():
            messages.error(request, 'This role is assigned to users and cannot be deleted.')
        else:
            role.delete()
            messages.success(request, 'CRM role deleted successfully.')
    return redirect('crm_analytics:crm_role_list')
