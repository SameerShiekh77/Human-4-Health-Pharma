def crm_globals(request):
    """
    Injects expiry_alert_count into every template for the sidebar badge.
    Add to TEMPLATES['OPTIONS']['context_processors'] in settings.py:
        'your_project.context_processors.crm_globals'
    """
    if request.user.is_authenticated:
        try:
            from crm_analytics.models import ExpiryAlert
            count = ExpiryAlert.objects.filter(is_acknowledged=False).count()
        except Exception:
            count = 0
        return {'expiry_alert_count': count}
    return {}
