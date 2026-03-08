## ── crm_sales/urls.py ───────────────────────────────────────

from django.urls import path
from . import views

app_name = 'crm_sales'

urlpatterns = [
    # Regions
    path('regions/',                  views.region_list,   name='region_list'),
    path('regions/create/',           views.region_create, name='region_create'),
    path('regions/<int:pk>/edit/',    views.region_edit,   name='region_edit'),
    path('regions/<int:pk>/delete/',  views.region_delete, name='region_delete'),

    # Areas
    path('areas/',                    views.area_list,   name='area_list'),
    path('areas/create/',             views.area_create, name='area_create'),
    path('areas/<int:pk>/edit/',      views.area_edit,   name='area_edit'),
    path('areas/<int:pk>/delete/',    views.area_delete, name='area_delete'),

    # Medical Reps
    path('mrs/',                      views.mr_list,   name='mr_list'),
    path('mrs/create/',               views.mr_create, name='mr_create'),
    path('mrs/<int:pk>/',             views.mr_detail, name='mr_detail'),
    path('mrs/<int:pk>/edit/',        views.mr_edit,   name='mr_edit'),
    path('mrs/<int:pk>/delete/',      views.mr_delete, name='mr_delete'),
]