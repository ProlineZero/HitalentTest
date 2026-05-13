from django.contrib import admin

from department.models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent', 'created_at')
    search_fields = ('name',)
