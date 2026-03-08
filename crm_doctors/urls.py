
## ── crm_doctors/urls.py ─────────────────────────────────────

from django.urls import path
from . import views

app_name = 'crm_doctors'

urlpatterns = [
    # Doctors
    path('',                       views.doctor_list,   name='doctor_list'),
    path('create/',                views.doctor_create, name='doctor_create'),
    path('<int:pk>/',              views.doctor_detail, name='doctor_detail'),
    path('<int:pk>/edit/',         views.doctor_edit,   name='doctor_edit'),
    path('<int:pk>/delete/',       views.doctor_delete, name='doctor_delete'),

    # Doctor Visits
    path('visits/',                views.visit_list,   name='visit_list'),
    path('visits/create/',         views.visit_create, name='visit_create'),
    path('visits/<int:pk>/',       views.visit_detail, name='visit_detail'),
    path('visits/<int:pk>/edit/',  views.visit_edit,   name='visit_edit'),
    path('visits/<int:pk>/delete/',views.visit_delete, name='visit_delete'),
]