
# uvicorn app.main:app --reload

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .config import Base, engine
from .models import User, Todo, PermissionType
from .schemas import UserCreate, UserShow, Token, TodoCreate, TodoUpdate, TodoShow, PermissionGrantRequest
from .auth import hash_password, verify_password, create_access_token
from .deps import get_db, get_current_user
from .crud import get_todo_by_id, user_has_permission, grant_permission, revoke_permission

from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI(title="ToDo API")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/register", response_model=UserShow)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/todos/", response_model=TodoShow)
async def create_todo(todo: TodoCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_todo = Todo(title=todo.title, description=todo.description, owner_id=current_user.id)
    db.add(new_todo)
    await db.commit()
    await db.refresh(new_todo)
    return new_todo

from sqlalchemy.orm import selectinload

@app.get("/todos/", response_model=list[TodoShow])
async def read_todos(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Todo).options(selectinload(Todo.permissions)))
    todos = []
    for todo in result.scalars().all():
        if await user_has_permission(db, todo, current_user.id, PermissionType.read) or \
           await user_has_permission(db, todo, current_user.id, PermissionType.update):
            todos.append(todo)
    return todos

@app.get("/todos/{todo_id}", response_model=TodoShow)
async def get_todo(todo_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if not (await user_has_permission(db, todo, current_user.id, PermissionType.read) or
            await user_has_permission(db, todo, current_user.id, PermissionType.update)):
        raise HTTPException(status_code=403, detail="Not enough rights")
    return todo

@app.put("/todos/{todo_id}", response_model=TodoShow)
async def update_todo(todo_id: int, todo_in: TodoUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if not await user_has_permission(db, todo, current_user.id, PermissionType.update):
        raise HTTPException(status_code=403, detail="Not enough rights")
    if todo_in.title is not None:
        todo.title = todo_in.title
    if todo_in.description is not None:
        todo.description = todo_in.description
    await db.commit()
    await db.refresh(todo)
    return todo

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete")
    await db.delete(todo)
    await db.commit()
    return {"detail": "Todo deleted"}

@app.post("/todos/{todo_id}/grant")
async def grant_todo_permission(todo_id: int, req: PermissionGrantRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can grant permissions")
    result = await db.execute(select(User).where(User.username == req.username))
    user2 = result.scalars().first()
    if not user2:
        raise HTTPException(status_code=404, detail="User not found")
    if user2.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot grant permission to yourself")
    await grant_permission(db, todo, user2, req.permission)
    return {"detail": f"Granted {req.permission} to {req.username}"}

@app.post("/todos/{todo_id}/revoke")
async def revoke_todo_permission(todo_id: int, req: PermissionGrantRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can revoke permissions")
    result = await db.execute(select(User).where(User.username == req.username))
    user2 = result.scalars().first()
    if not user2:
        raise HTTPException(status_code=404, detail="User not found")
    if user2.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot revoke permission from yourself")
    await revoke_permission(db, todo, user2, req.permission)
    return {"detail": f"Revoked {req.permission} from {req.username}"}