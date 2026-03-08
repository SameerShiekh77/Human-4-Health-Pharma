
## ── crm_distributors/urls.py ────────────────────────────────

from django.urls import path
from . import views

app_name = 'crm_distributors'

urlpatterns = [
    # Distributors
    path('',                       views.distributor_list,   name='distributor_list'),
    path('create/',                views.distributor_create, name='distributor_create'),
    path('<int:pk>/',              views.distributor_detail, name='distributor_detail'),
    path('<int:pk>/edit/',         views.distributor_edit,   name='distributor_edit'),
    path('<int:pk>/delete/',       views.distributor_delete, name='distributor_delete'),

    # Stock Entries
    path('stock-entries/',              views.stock_entry_list,   name='stock_entry_list'),
    path('stock-entries/create/',       views.stock_entry_create, name='stock_entry_create'),
    path('stock-entries/<int:pk>/',     views.stock_entry_detail, name='stock_entry_detail'),
    path('stock-entries/<int:pk>/edit/',   views.stock_entry_edit,   name='stock_entry_edit'),
    path('stock-entries/<int:pk>/delete/', views.stock_entry_delete, name='stock_entry_delete'),

    # Sales Values
    path('sales/',              views.sales_value_list,   name='sales_value_list'),
    path('sales/create/',       views.sales_value_create, name='sales_value_create'),
    path('sales/<int:pk>/delete/', views.sales_value_delete, name='sales_value_delete'),
]