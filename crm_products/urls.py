from django.urls import path
from . import views

app_name = 'crm_products'

urlpatterns = [
    # Divisions
    path('divisions/',             views.division_list,   name='division_list'),
    path('divisions/create/',      views.division_create, name='division_create'),
    path('divisions/<int:pk>/edit/',   views.division_edit,   name='division_edit'),
    path('divisions/<int:pk>/delete/', views.division_delete, name='division_delete'),

    # Products
    path('',                        views.product_list,   name='product_list'),
    path('create/',                 views.product_create, name='product_create'),
    path('<int:pk>/',               views.product_detail, name='product_detail'),
    path('<int:pk>/edit/',          views.product_edit,   name='product_edit'),
    path('<int:pk>/delete/',        views.product_delete, name='product_delete'),

    # Batches
    path('batches/',                views.batch_list,   name='batch_list'),
    path('batches/create/',         views.batch_create, name='batch_create'),
    path('batches/<int:pk>/',       views.batch_detail, name='batch_detail'),
    path('batches/<int:pk>/edit/',  views.batch_edit,   name='batch_edit'),
    path('batches/<int:pk>/delete/',views.batch_delete, name='batch_delete'),

    # Company Stock
    path('stock/',                  views.stock_list,   name='stock_list'),
    path('stock/create/',           views.stock_create, name='stock_create'),
    path('stock/<int:pk>/edit/',    views.stock_edit,   name='stock_edit'),
    path('stock/<int:pk>/delete/',  views.stock_delete, name='stock_delete'),
]