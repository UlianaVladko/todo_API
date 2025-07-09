# ToDo API

## Быстрый запуск

1. **Создание БД PostgreSQL**  
   Через psql или графический интерфейс pgAdmin:
   ```
   CREATE DATABASE todo_db;
   ```

2. **Установка зависимости**
   ```
   pip install -r requirements.txt
   ```

3. **Настройка DATABASE_URL и alembic.ini**  
   В `app/config.py` 
   заменить
   ```
   `DATABASE_URL = "postgresql+asyncpg://postgres:myCotValerasiniy1007@localhost:5432/todo_db"`
   ```
   на свой пароль
   ```
   `DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/name_of_file"`
   ```
   В `alembic.ini`
   заменить
   ```
   `sqlalchemy.url = postgresql+asyncpg://postgres:myCotValerasiniy1007@localhost:5432/todo_db`
   ```
   на свой пароль
   ```
   `sqlalchemy.url = postgresql+asyncpg://postgres:password@localhost:5432/name_of_file`
   ```



5. **Миграции БД**
   ```
   alembic upgrade head
   ```

6. **Запуск**
   ```
   uvicorn app.main:app --reload
   ```

7. **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Тесты

```
$env:PYTHONPATH = "."; pytest -v
```

## Функционал

- Регистрация / Логин (JWT)
- CRUD для задач
- Права доступа (read/update) к задачам другим пользователям
- Только владелец может выдавать/забирать права

## Запросы

- **POST /register** — регистрация  
- **POST /login** — логин, получение токена  
- **POST /todos/** — создать задачу  
- **GET /todos/** — посмотреть список задач
- **GET /todos/{id}** — посмотреть задачи по id  
- **PUT /todos/{id}** — обновить задачу (если есть право update или задача ваша) 
- **DELETE /todos/{id}** — удалить задачу  
- **POST /todos/{id}/grant** — выдать права другому пользователю  
- **POST /todos/{id}/revoke** — отозвать права  
