from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse

from hr.models import (
    Department, Position, Employee,
)
# Create your views here.

# ============================================
# HR MODULE - DEPARTMENT VIEWS
# ============================================

@staff_member_required(login_url='login')
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'dashboard/hr/department_list.html', {'departments': departments})


@staff_member_required(login_url='login')
def department_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        Department.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )
        messages.success(request, 'Department created successfully.')
        return redirect('department_list')
    
    return render(request, 'dashboard/hr/department_form.html', {'action': 'Create'})


@staff_member_required(login_url='login')
def department_edit(request, id):
    department = get_object_or_404(Department, id=id)
    
    if request.method == 'POST':
        department.name = request.POST.get('name')
        department.description = request.POST.get('description')
        department.is_active = request.POST.get('is_active') == 'on'
        department.save()
        messages.success(request, 'Department updated successfully.')
        return redirect('department_list')
    
    return render(request, 'dashboard/hr/department_form.html', {
        'department': department,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def department_delete(request, id):
    department = get_object_or_404(Department, id=id)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully.')
    return redirect('department_list')


# ============================================
# HR MODULE - POSITION VIEWS
# ============================================

@staff_member_required(login_url='login')
def position_list(request):
    positions = Position.objects.select_related('department').all()
    return render(request, 'dashboard/hr/position_list.html', {'positions': positions})


@staff_member_required(login_url='login')
def position_create(request):
    departments = Department.objects.filter(is_active=True)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        department_id = request.POST.get('department')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        Position.objects.create(
            title=title,
            department_id=department_id,
            description=description,
            is_active=is_active
        )
        messages.success(request, 'Position created successfully.')
        return redirect('position_list')
    
    return render(request, 'dashboard/hr/position_form.html', {
        'departments': departments,
        'action': 'Create'
    })


@staff_member_required(login_url='login')
def position_edit(request, id):
    position = get_object_or_404(Position, id=id)
    departments = Department.objects.filter(is_active=True)
    
    if request.method == 'POST':
        position.title = request.POST.get('title')
        position.department_id = request.POST.get('department')
        position.description = request.POST.get('description')
        position.is_active = request.POST.get('is_active') == 'on'
        position.save()
        messages.success(request, 'Position updated successfully.')
        return redirect('position_list')
    
    return render(request, 'dashboard/hr/position_form.html', {
        'position': position,
        'departments': departments,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def position_delete(request, id):
    position = get_object_or_404(Position, id=id)
    if request.method == 'POST':
        position.delete()
        messages.success(request, 'Position deleted successfully.')
    return redirect('position_list')


# ============================================
# HR MODULE - EMPLOYEE VIEWS
# ============================================

@staff_member_required(login_url='login')
def employee_list(request):
    employees = Employee.objects.select_related('user', 'department', 'position').all()
    return render(request, 'dashboard/hr/employee_list.html', {'employees': employees})


@staff_member_required(login_url='login')
def employee_create(request):
    departments = Department.objects.filter(is_active=True)
    positions = Position.objects.filter(is_active=True)
    users_without_profile = User.objects.filter(employee_profile__isnull=True)
    
    if request.method == 'POST':
        user_id = request.POST.get('user')
        employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department')
        position_id = request.POST.get('position')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        date_of_birth = request.POST.get('date_of_birth') or None
        hire_date = request.POST.get('hire_date') or None
        is_active = request.POST.get('is_active') == 'on'
        
        employee = Employee.objects.create(
            user_id=user_id,
            employee_id=employee_id,
            department_id=department_id if department_id else None,
            position_id=position_id if position_id else None,
            phone=phone,
            address=address,
            date_of_birth=date_of_birth,
            hire_date=hire_date,
            is_active=is_active
        )
        
        if request.FILES.get('profile_image'):
            employee.profile_image = request.FILES.get('profile_image')
            employee.save()
        
        messages.success(request, 'Employee created successfully.')
        return redirect('employee_list')
    
    return render(request, 'dashboard/hr/employee_form.html', {
        'departments': departments,
        'positions': positions,
        'users': users_without_profile,
        'action': 'Create'
    })


@staff_member_required(login_url='login')
def employee_edit(request, id):
    employee = get_object_or_404(Employee, id=id)
    departments = Department.objects.filter(is_active=True)
    positions = Position.objects.filter(is_active=True)
    
    if request.method == 'POST':
        employee.employee_id = request.POST.get('employee_id')
        employee.department_id = request.POST.get('department') or None
        employee.position_id = request.POST.get('position') or None
        employee.phone = request.POST.get('phone')
        employee.address = request.POST.get('address')
        employee.date_of_birth = request.POST.get('date_of_birth') or None
        employee.hire_date = request.POST.get('hire_date') or None
        employee.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('profile_image'):
            employee.profile_image = request.FILES.get('profile_image')
        
        employee.save()
        messages.success(request, 'Employee updated successfully.')
        return redirect('employee_list')
    
    return render(request, 'dashboard/hr/employee_form.html', {
        'employee': employee,
        'departments': departments,
        'positions': positions,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def employee_detail(request, id):
    employee = get_object_or_404(Employee, id=id)
    return render(request, 'dashboard/hr/employee_detail.html', {'employee': employee})


@staff_member_required(login_url='login')
def employee_delete(request, id):
    employee = get_object_or_404(Employee, id=id)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
    return redirect('employee_list')

