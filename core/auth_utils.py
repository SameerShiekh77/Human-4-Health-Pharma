from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import Permission
from django.shortcuts import redirect


CRM_ROLE_PREFIX = 'CRM -'


CRM_URL_PERMISSION_RULES = {
    'crm_products': {
        'division_': ('crm_products', 'division'),
        'product_': ('crm_products', 'productmaster'),
        'batch_': ('crm_products', 'batchmanagement'),
        'stock_': ('crm_products', 'companystock'),
    },
    'crm_distributors': {
        'distributor_': ('crm_distributors', 'distributor'),
        'stock_entry_': ('crm_distributors', 'distributorstockentry'),
        'sales_value_': ('crm_distributors', 'distributorsalesvalue'),
    },
    'crm_sales': {
        'region_': ('crm_sales', 'region'),
        'area_': ('crm_sales', 'area'),
        'mr_': ('crm_sales', 'medicalrepresentative'),
    },
    'crm_doctors': {
        'doctor_': ('crm_doctors', 'doctor'),
        'visit_': ('crm_doctors', 'doctorvisit'),
    },
    'crm_stores': {
        'store_': ('crm_stores', 'medicalstore'),
    },
}


CRM_ANALYTICS_PERMISSION_RULES = {
    'mr_performance': 'crm_analytics.view_mrperformancesnapshot',
    'doctor_performance': 'crm_analytics.view_doctorperformancesnapshot',
    'distributor_performance': 'crm_analytics.view_distributorperformancesnapshot',
    'product_performance': 'crm_analytics.view_productperformancesnapshot',
    'expiry_alerts': 'crm_analytics.view_expiryalert',
    'acknowledge_alert': 'crm_analytics.change_expiryalert',
    'crm_user_list': 'auth.view_user',
    'crm_user_create': 'auth.add_user',
    'crm_user_edit': 'auth.change_user',
    'crm_user_delete': 'auth.delete_user',
    'crm_role_list': 'auth.view_group',
    'crm_role_create': 'auth.add_group',
    'crm_role_edit': 'auth.change_group',
    'crm_role_delete': 'auth.delete_group',
}


CRM_ROLE_PERMISSION_GROUPS = [
    {
        'title': 'Products',
        'items': [
            {'label': 'Territories', 'app_label': 'crm_products', 'model': 'division'},
            {'label': 'Products', 'app_label': 'crm_products', 'model': 'productmaster'},
            {'label': 'Batches', 'app_label': 'crm_products', 'model': 'batchmanagement'},
            {'label': 'Company Stock', 'app_label': 'crm_products', 'model': 'companystock'},
        ],
    },
    {
        'title': 'Distribution',
        'items': [
            {'label': 'Distributors', 'app_label': 'crm_distributors', 'model': 'distributor'},
            {'label': 'Stock Entries', 'app_label': 'crm_distributors', 'model': 'distributorstockentry'},
            {'label': 'Sales Records', 'app_label': 'crm_distributors', 'model': 'distributorsalesvalue'},
        ],
    },
    {
        'title': 'Sales Force',
        'items': [
            {'label': 'Regions', 'app_label': 'crm_sales', 'model': 'region'},
            {'label': 'Areas', 'app_label': 'crm_sales', 'model': 'area'},
            {'label': 'Medical Reps', 'app_label': 'crm_sales', 'model': 'medicalrepresentative'},
        ],
    },
    {
        'title': 'Field Activity',
        'items': [
            {'label': 'Doctors', 'app_label': 'crm_doctors', 'model': 'doctor'},
            {'label': 'Visits', 'app_label': 'crm_doctors', 'model': 'doctorvisit'},
        ],
    },
    {
        'title': 'Retail',
        'items': [
            {'label': 'Medical Stores', 'app_label': 'crm_stores', 'model': 'medicalstore'},
        ],
    },
    {
        'title': 'Analytics',
        'items': [
            {'label': 'MR Performance', 'app_label': 'crm_analytics', 'model': 'mrperformancesnapshot'},
            {'label': 'Doctor ROI', 'app_label': 'crm_analytics', 'model': 'doctorperformancesnapshot'},
            {'label': 'Distributor Performance', 'app_label': 'crm_analytics', 'model': 'distributorperformancesnapshot'},
            {'label': 'Product Performance', 'app_label': 'crm_analytics', 'model': 'productperformancesnapshot'},
            {'label': 'Expiry Alerts', 'app_label': 'crm_analytics', 'model': 'expiryalert'},
        ],
    },
    {
        'title': 'Access Control',
        'items': [
            {'label': 'CRM Users', 'app_label': 'auth', 'model': 'user'},
            {'label': 'CRM Roles', 'app_label': 'auth', 'model': 'group'},
        ],
    },
]


def is_crm_user(user):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__istartswith=CRM_ROLE_PREFIX).exists()


def _resolve_action_from_url_name(url_name):
    if url_name.endswith('_create') or url_name.endswith('_add'):
        return 'add'
    if url_name.endswith('_edit') or url_name.endswith('_update'):
        return 'change'
    if url_name.endswith('_delete'):
        return 'delete'
    return 'view'


def _resolve_crm_permission_from_route(request):
    match = getattr(request, 'resolver_match', None)
    if not match:
        return None

    namespace = match.namespace
    url_name = match.url_name or ''

    if namespace == 'crm_analytics':
        return CRM_ANALYTICS_PERMISSION_RULES.get(url_name)

    rules = CRM_URL_PERMISSION_RULES.get(namespace, {})
    for prefix, (app_label, model_name) in rules.items():
        if url_name.startswith(prefix):
            action = _resolve_action_from_url_name(url_name)
            return f'{app_label}.{action}_{model_name}'

    return None


def get_crm_permission_groups():
    grouped = []
    for section in CRM_ROLE_PERMISSION_GROUPS:
        section_items = []
        for item in section['items']:
            perms = {}
            for action in ('view', 'add', 'change', 'delete'):
                codename = f'{action}_{item["model"]}'
                perm = Permission.objects.filter(
                    content_type__app_label=item['app_label'],
                    codename=codename,
                ).first()
                if perm:
                    perms[action] = perm

            if perms:
                section_items.append({
                    'label': item['label'],
                    'permissions': perms,
                })

        if section_items:
            grouped.append({
                'title': section['title'],
                'items': section_items,
            })

    return grouped


def get_crm_allowed_permission_ids():
    allowed_ids = set()
    for section in get_crm_permission_groups():
        for item in section['items']:
            for perm in item['permissions'].values():
                allowed_ids.add(perm.id)
    return allowed_ids


def crm_access_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_crm_user(request.user):
            return redirect('crm_analytics:crm_login')

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        required_perm = _resolve_crm_permission_from_route(request)
        if required_perm and not request.user.has_perm(required_perm):
            messages.error(request, 'You do not have permission to access that CRM section.')
            return redirect('crm_analytics:dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
