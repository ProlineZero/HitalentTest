import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from department.models import Department
from department.serializers import (
    DepartmentCreateSerializer,
    DepartmentPatchSerializer,
    DepartmentSerializer,
    EmployeeCreateSerializer,
    EmployeeSerializer,
)
from employee.models import Employee

logger = logging.getLogger('department')


def _parse_depth(raw: str | None) -> int:
    if raw is None:
        return 1
    try:
        value = int(raw)
    except ValueError:
        return 1
    return max(0, min(5, value))


def _parse_include_employees(raw: str | None) -> bool:
    if raw is None:
        return True
    return raw.lower() in ('1', 'true', 'yes')


def build_department_subtree(department: Department, depth: int, include_employees: bool) -> dict:
    payload: dict = {
        'department': DepartmentSerializer(department).data,
        'employees': [],
        'children': [],
    }
    if include_employees:
        employees = department.employees.order_by('created_at', 'full_name')
        payload['employees'] = EmployeeSerializer(employees, many=True).data
    if depth > 0:
        for child in department.children.order_by('id'):
            payload['children'].append(
                build_department_subtree(child, depth - 1, include_employees),
            )
    return payload


class DepartmentCreateView(APIView):
    def post(self, request):
        serializer = DepartmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        logger.info('Создано подразделение id=%s name=%s', department.id, department.name)
        return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)


class DepartmentDetailView(APIView):
    def get(self, request, department_id: int):
        department = get_object_or_404(Department, pk=department_id)
        depth = _parse_depth(request.query_params.get('depth'))
        include_employees = _parse_include_employees(request.query_params.get('include_employees'))
        payload = build_department_subtree(department, depth, include_employees)
        return Response(payload)

    def patch(self, request, department_id: int):
        department = get_object_or_404(Department, pk=department_id)
        serializer = DepartmentPatchSerializer(
            data=request.data,
            partial=True,
            context={'department': department},
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.update(department, serializer.validated_data)
        logger.info('Обновлено подразделение id=%s', updated.id)
        return Response(DepartmentSerializer(updated).data)

    def delete(self, request, department_id: int):
        mode = request.query_params.get('mode')
        if mode not in ('cascade', 'reassign'):
            return Response(
                {'detail': 'Укажите query-параметр mode=cascade или mode=reassign'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        department = get_object_or_404(Department, pk=department_id)
        if mode == 'cascade':
            department.delete()
            logger.info('Каскадное удаление подразделения id=%s', department_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        raw_target = request.query_params.get('reassign_to_department_id')
        if raw_target is None:
            return Response(
                {'detail': 'Для mode=reassign укажите reassign_to_department_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            target_id = int(raw_target)
        except ValueError:
            return Response(
                {'detail': 'reassign_to_department_id должен быть целым числом'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if target_id == department.id:
            return Response(
                {'detail': 'reassign_to_department_id не может совпадать с удаляемым подразделением'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not Department.objects.filter(pk=target_id).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        Employee.objects.filter(department=department).update(department_id=target_id)
        Department.objects.filter(parent=department).update(parent_id=department.parent_id)
        department.delete()
        logger.info('Удалено подразделение id=%s с переносом сотрудников в %s', department_id, target_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DepartmentEmployeeCreateView(APIView):
    def post(self, request, department_id: int):
        department = get_object_or_404(Department, pk=department_id)
        serializer = EmployeeCreateSerializer(
            data=request.data,
            context={'department': department},
        )
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        logger.info('Создан сотрудник id=%s в подразделении %s', employee.id, department_id)
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)