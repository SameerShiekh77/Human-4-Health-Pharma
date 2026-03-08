
## ── crm_analytics/urls.py ───────────────────────────────────

from django.urls import path
from . import views

app_name = 'crm_analytics'

urlpatterns = [
    path('',                         views.dashboard,               name='dashboard'),
    path('mr-performance/',          views.mr_performance,          name='mr_performance'),
    path('doctor-performance/',      views.doctor_performance,      name='doctor_performance'),
    path('distributor-performance/', views.distributor_performance, name='distributor_performance'),
    path('product-performance/',     views.product_performance,     name='product_performance'),
    path('expiry-alerts/',           views.expiry_alerts,           name='expiry_alerts'),
    path('expiry-alerts/<int:pk>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
]
