# HitalentTest

API организационной структуры: подразделения (дерево) и сотрудники. Стек: Django, Django REST Framework, PostgreSQL.

## Запуск в Docker

```bash
docker compose up --build
```

Приложение: порт **8000**. Параметры подключения к PostgreSQL — в `docker-compose.yml`; порт **5432** сервиса БД проброшен на хост для локальной разработки и тестов.

Перед стартом в контейнере выполняются миграции. Создание суперпользователя для админки:

```bash
docker compose exec web python manage.py createsuperuser
```

## REST API и документация

Эндпоинты подразделений без префикса `/api` (например, `/departments/`). Для маршрутов Django задан завершающий слэш; запрос без него может вернуть редирект.

- OpenAPI: `/api/schema/`
- Swagger UI: `/api/docs/`

## Локальный запуск без Docker

Требуется установленный PostgreSQL. Настройки БД задаются переменными окружения `POSTGRES_*` (см. `config/settings.py`).

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Пример задания пароля в PowerShell:

```powershell
$env:POSTGRES_PASSWORD = '<пароль>'
python manage.py runserver
```

Тесты: `pytest` (нужен доступ к той же БД с теми же учётными данными).

## Поведение API (кратко)

- Удаление с параметром `mode=reassign`: сотрудники переносятся в указанное подразделение; прямые дочерние подразделения привязываются к бывшему родителю удаляемого узла; затем узел удаляется.
- Попытка зациклить иерархию при смене родителя возвращает **409 Conflict**.
