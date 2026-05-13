import pytest
from rest_framework import status
from rest_framework.test import APIClient

from department.models import Department
from employee.models import Employee


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_create_department_and_employee_tree_and_cascade(api_client: APIClient) -> None:
    r = api_client.post('/departments/', {'name': 'Root'}, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    root_id = r.data['id']

    r = api_client.post(f'/departments/{root_id}/employees/', {'full_name': 'Иван', 'position': 'Инженер'}, format='json')
    assert r.status_code == status.HTTP_201_CREATED

    r = api_client.post('/departments/', {'name': 'Child', 'parent_id': root_id}, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    child_id = r.data['id']

    r = api_client.get(f'/departments/{root_id}/', {'depth': '2'})
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data['children']) == 1
    assert r.data['children'][0]['department']['id'] == child_id

    r = api_client.delete(f'/departments/{root_id}/?mode=cascade')
    assert r.status_code == status.HTTP_204_NO_CONTENT
    assert Department.objects.count() == 0
    assert Employee.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_name_same_parent_conflict(api_client: APIClient) -> None:
    r = api_client.post('/departments/', {'name': 'Same'}, format='json')
    assert r.status_code == status.HTTP_201_CREATED
    r = api_client.post('/departments/', {'name': 'Same'}, format='json')
    assert r.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_move_department_cycle_conflict(api_client: APIClient) -> None:
    root = Department.objects.create(name='R')
    a = Department.objects.create(name='A', parent=root)
    b = Department.objects.create(name='B', parent=a)
    r = api_client.patch(f'/departments/{a.id}/', {'parent_id': b.id}, format='json')
    assert r.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_delete_reassign_employees(api_client: APIClient) -> None:
    d1 = Department.objects.create(name='D1')
    d2 = Department.objects.create(name='D2')
    Employee.objects.create(department=d1, full_name='U1', position='P')
    r = api_client.delete(
        f'/departments/{d1.id}/?mode=reassign&reassign_to_department_id={d2.id}',
    )
    assert r.status_code == status.HTTP_204_NO_CONTENT
    assert not Department.objects.filter(pk=d1.id).exists()
    assert Employee.objects.filter(department=d2, full_name='U1').exists()


@pytest.mark.django_db
def test_create_employee_unknown_department_404(api_client: APIClient) -> None:
    r = api_client.post('/departments/99999/employees/', {'full_name': 'X', 'position': 'Y'}, format='json')
    assert r.status_code == status.HTTP_404_NOT_FOUND
