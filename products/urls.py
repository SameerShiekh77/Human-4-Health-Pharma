
from django.urls import path
from . import views

urlpatterns = [
      # Product Module
    path('', views.product_list_dashboard, name='product_list_dashboard'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:id>/delete/', views.product_delete, name='product_delete'),
    path('products/images/<int:id>/delete/', views.product_image_delete, name='product_image_delete'),
    
    # Product Module - Categories
    path('products/categories/', views.product_category_list, name='product_category_list'),
    path('products/categories/create/', views.product_category_create, name='product_category_create'),
    path('products/categories/<int:id>/edit/', views.product_category_edit, name='product_category_edit'),
    path('products/categories/<int:id>/delete/', views.product_category_delete, name='product_category_delete'),
    
]