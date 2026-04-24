
## ── crm_analytics/urls.py ───────────────────────────────────

from django.urls import path
from . import views

app_name = 'crm_analytics'

urlpatterns = [
    path('',                         views.dashboard,               name='dashboard'),
    path('login/',                   views.crm_login,               name='crm_login'),
    path('logout/',                  views.crm_logout,              name='crm_logout'),
    path('users/',                   views.crm_user_list,           name='crm_user_list'),
    path('users/create/',            views.crm_user_create,         name='crm_user_create'),
    path('users/<int:id>/edit/',     views.crm_user_edit,           name='crm_user_edit'),
    path('users/<int:id>/delete/',   views.crm_user_delete,         name='crm_user_delete'),
    path('roles/',                   views.crm_role_list,           name='crm_role_list'),
    path('roles/create/',            views.crm_role_create,         name='crm_role_create'),
    path('roles/<int:id>/edit/',     views.crm_role_edit,           name='crm_role_edit'),
    path('roles/<int:id>/delete/',   views.crm_role_delete,         name='crm_role_delete'),
    path('mr-performance/',          views.mr_performance,          name='mr_performance'),
    path('doctor-performance/',      views.doctor_performance,      name='doctor_performance'),
    path('distributor-performance/', views.distributor_performance, name='distributor_performance'),
    path('product-performance/',     views.product_performance,     name='product_performance'),
    path('expiry-alerts/',           views.expiry_alerts,           name='expiry_alerts'),
    path('expiry-alerts/<int:pk>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
]
