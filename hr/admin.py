from django.contrib import admin
from .models import (
    Department, Position, Employee,
)


# ============================================
# HR MODULE ADMIN
# ============================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'employee_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'is_active', 'created_at']
    list_filter = ['is_active', 'department']
    search_fields = ['title', 'description']
    ordering = ['title']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'department', 'position', 'is_active', 'hire_date']
    list_filter = ['is_active', 'department', 'position']
    search_fields = ['employee_id', 'user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    ordering = ['-created_at']
