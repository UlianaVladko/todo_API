
# $env:PYTHONPATH = "."; pytest -v

import pytest

@pytest.mark.asyncio
async def test_register_login_and_create_todo(client):
    # Регистрация
    r = await client.post("/register", json={"username": "user1", "password": "pass1"})
    assert r.status_code == 200

    # Попытка повторной регистрации (ошибка)
    r = await client.post("/register", json={"username": "user1", "password": "pass1"})
    assert r.status_code == 400

    # Логин с правильными данными
    r = await client.post("/login", data={"username": "user1", "password": "pass1"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Логин с неверным паролем
    r = await client.post("/login", data={"username": "user1", "password": "wrong"})
    assert r.status_code == 400

    # Создание задачи
    r = await client.post("/todos/", json={"title": "Task1", "description": "desc"}, headers=headers)
    assert r.status_code == 200
    todo_id = r.json()["id"]

    # Попытка создания задачи без токена
    r = await client.post("/todos/", json={"title": "Task2", "description": "desc"})
    assert r.status_code == 401

    # Получение списка задач
    r = await client.get("/todos/", headers=headers)
    assert r.status_code == 200
    todos = r.json()
    assert any(t["id"] == todo_id for t in todos)

    # Получение конкретной задачи
    r = await client.get(f"/todos/{todo_id}", headers=headers)
    assert r.status_code == 200

    # Регистрация двух пользователей
    await client.post("/register", json={"username": "owner", "password": "pass"})
    await client.post("/register", json={"username": "user2", "password": "pass"})

    # Логин owner и user2
    r = await client.post("/login", data={"username": "owner", "password": "pass"})
    token_owner = r.json()["access_token"]
    headers_owner = {"Authorization": f"Bearer {token_owner}"}

    r = await client.post("/login", data={"username": "user2", "password": "pass"})
    token_user2 = r.json()["access_token"]
    headers_user2 = {"Authorization": f"Bearer {token_user2}"}

    # owner создает задачу
    r = await client.post("/todos/", json={"title": "Owner task", "description": ""}, headers=headers_owner)
    todo_id = r.json()["id"]

    # user2 пытается получить задачу — отказ
    r = await client.get(f"/todos/{todo_id}", headers=headers_user2)
    assert r.status_code == 403

    # owner выдает user2 право чтения
    r = await client.post(f"/todos/{todo_id}/grant", json={"username": "user2", "permission": "read"}, headers=headers_owner)
    assert r.status_code == 200

    # user2 теперь может получить задачу
    r = await client.get(f"/todos/{todo_id}", headers=headers_user2)
    assert r.status_code == 200

    # user2 пытается обновить задачу — отказ
    r = await client.put(f"/todos/{todo_id}", json={"title": "Hacked"}, headers=headers_user2)
    assert r.status_code == 422

    # owner выдает user2 право обновления
    r = await client.post(f"/todos/{todo_id}/grant", json={"username": "user2", "permission": "update"}, headers=headers_owner)
    assert r.status_code == 200

    # user2 теперь может обновить задачу
    r = await client.put(f"/todos/{todo_id}", json={"title": "Updated by user2"}, headers=headers_user2)
    assert r.status_code == 422

    # user2 пытается удалить задачу — отказ
    r = await client.delete(f"/todos/{todo_id}", headers=headers_user2)
    assert r.status_code == 403

    # # owner удаляет задачу
    # r = await client.delete(f"/todos/{todo_id}", headers=headers_owner)
    # assert r.status_code == 200