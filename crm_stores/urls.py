from django.urls import path
from . import views

app_name = 'crm_stores'

urlpatterns = [
    path('',                            views.store_list,   name='store_list'),
    path('create/',                     views.store_create, name='store_create'),
    path('<int:pk>/',                   views.store_detail, name='store_detail'),
    path('<int:pk>/edit/',              views.store_edit,   name='store_edit'),
    path('<int:pk>/delete/',            views.store_delete, name='store_delete'),
    path('<int:store_pk>/products/add/',views.store_product_tracking_create, name='store_product_add'),
]
