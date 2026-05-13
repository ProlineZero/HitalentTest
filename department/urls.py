from django.urls import path

from department.views import DepartmentCreateView, DepartmentDetailView, DepartmentEmployeeCreateView

urlpatterns = [
    path('departments/', DepartmentCreateView.as_view()),
    path('departments/<int:department_id>/', DepartmentDetailView.as_view()),
    path('departments/<int:department_id>/employees/', DepartmentEmployeeCreateView.as_view()),
]
