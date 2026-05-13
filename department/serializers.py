from django.db import IntegrityError
from rest_framework import serializers

from department.exceptions import ConflictError
from department.models import Department
from department.utils import trim_non_empty, would_create_cycle
from employee.models import Employee


class DepartmentSerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(source='parent.id', read_only=True, allow_null=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'parent_id', 'created_at']


class DepartmentCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    parent_id = serializers.IntegerField(required=False, allow_null=True, default=None)

    def validate_name(self, value: str) -> str:
        try:
            return trim_non_empty(value, 'Название подразделения')
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_parent_id(self, value: int | None) -> int | None:
        if value is None:
            return value
        if not Department.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Родительское подразделение не найдено')
        return value

    def validate(self, attrs: dict) -> dict:
        parent_id = attrs.get('parent_id')
        name = attrs['name']
        if self._name_exists_under_parent(name, parent_id):
            raise ConflictError('Название должно быть уникальным в рамках одного родителя')
        return attrs

    @staticmethod
    def _name_exists_under_parent(name: str, parent_id: int | None) -> bool:
        if parent_id is None:
            return Department.objects.filter(parent__isnull=True, name=name).exists()
        return Department.objects.filter(parent_id=parent_id, name=name).exists()

    def create(self, validated_data: dict) -> Department:
        parent_id = validated_data.pop('parent_id', None)
        name = validated_data['name']
        try:
            return Department.objects.create(name=name, parent_id=parent_id)
        except IntegrityError as exc:
            raise ConflictError(
                'Название должно быть уникальным в рамках одного родителя',
            ) from exc


class DepartmentPatchSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    parent_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_name(self, value: str) -> str:
        try:
            return trim_non_empty(value, 'Название подразделения')
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_parent_id(self, value: int | None) -> int | None:
        if value is None:
            return value
        if not Department.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Родительское подразделение не найдено')
        return value

    def validate(self, attrs: dict) -> dict:
        instance: Department = self.context['department']
        name = attrs.get('name', instance.name)
        parent_id = attrs['parent_id'] if 'parent_id' in attrs else instance.parent_id

        if DepartmentPatchSerializer._name_exists_under_parent_for_update(instance.pk, name, parent_id):
            raise ConflictError('Название должно быть уникальным в рамках одного родителя')

        new_parent = attrs['parent_id'] if 'parent_id' in attrs else instance.parent_id
        if would_create_cycle(instance.pk, new_parent):
            raise ConflictError('Нельзя сделать подразделение родителем самого себя или создать цикл')

        return attrs

    def update(self, instance: Department, validated_data: dict) -> Department:
        if 'name' in validated_data:
            instance.name = validated_data['name']
        if 'parent_id' in validated_data:
            instance.parent_id = validated_data['parent_id']
        try:
            instance.save()
        except IntegrityError as exc:
            raise ConflictError(
                'Название должно быть уникальным в рамках одного родителя',
            ) from exc
        return instance

    @staticmethod
    def _name_exists_under_parent_for_update(
        department_pk: int,
        name: str,
        parent_id: int | None,
    ) -> bool:
        if parent_id is None:
            qs = Department.objects.filter(parent__isnull=True, name=name)
        else:
            qs = Department.objects.filter(parent_id=parent_id, name=name)
        return qs.exclude(pk=department_pk).exists()


class EmployeeSerializer(serializers.ModelSerializer):
    department_id = serializers.IntegerField(source='department.id', read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'department_id', 'full_name', 'position', 'hired_at', 'created_at']


class EmployeeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['full_name', 'position', 'hired_at']

    def validate_full_name(self, value: str) -> str:
        try:
            return trim_non_empty(value, 'ФИО')
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_position(self, value: str) -> str:
        try:
            return trim_non_empty(value, 'Должность')
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def create(self, validated_data: dict) -> Employee:
        return Employee.objects.create(
            department=self.context['department'],
            **validated_data,
        )
