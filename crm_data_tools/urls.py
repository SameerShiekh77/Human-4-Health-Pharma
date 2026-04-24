from django.urls import path
from . import views

app_name = 'crm_data_tools'

urlpatterns = [
    path('<slug:model_key>/export/', views.export_csv, name='export'),
    path('<slug:model_key>/sample/', views.sample_csv, name='sample'),
    path('<slug:model_key>/import/', views.import_upload, name='import'),
]
