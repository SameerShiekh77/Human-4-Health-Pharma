
from django.urls import path
from . import views

urlpatterns = [
    
    # HR Module - Departments
    path('', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:id>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:id>/delete/', views.department_delete, name='department_delete'),
    
    # HR Module - Positions
    path('positions/', views.position_list, name='position_list'),
    path('positions/create/', views.position_create, name='position_create'),
    path('positions/<int:id>/edit/', views.position_edit, name='position_edit'),
    path('positions/<int:id>/delete/', views.position_delete, name='position_delete'),
    
    # HR Module - Employees
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:id>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:id>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:id>/delete/', views.employee_delete, name='employee_delete'),
]