from django.contrib import admin

from employee.models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'department', 'position', 'hired_at', 'created_at')
    search_fields = ('full_name', 'position')
