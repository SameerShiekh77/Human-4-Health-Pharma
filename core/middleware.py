from django.shortcuts import redirect

from core.auth_utils import is_crm_user


class CRMAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/crm/') and path not in {'/crm/login/', '/crm/logout/'}:
            if not request.user.is_authenticated or not is_crm_user(request.user):
                return redirect('crm_analytics:crm_login')
        return self.get_response(request)
