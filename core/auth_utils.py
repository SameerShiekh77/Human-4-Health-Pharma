from functools import wraps

from django.shortcuts import redirect


CRM_ROLE_PREFIX = 'CRM -'


def is_crm_user(user):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__istartswith=CRM_ROLE_PREFIX).exists()


def crm_access_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if is_crm_user(request.user):
            return view_func(request, *args, **kwargs)
        return redirect('crm_analytics:crm_login')

    return _wrapped_view
