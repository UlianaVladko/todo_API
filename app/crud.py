
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound
from .models import Todo, User, TodoPermission, PermissionType

async def get_todo_by_id(db: AsyncSession, todo_id: int):
    result = await db.execute(select(Todo).options(selectinload(Todo.permissions)).where(Todo.id == todo_id))
    return result.scalars().first()

async def user_has_permission(db: AsyncSession, todo: Todo, user_id: int, perm: PermissionType):
    if todo.owner_id == user_id:
        return True
    for p in todo.permissions:
        if p.user_id == user_id and p.permission == perm:
            return True
    return False

async def grant_permission(db: AsyncSession, todo: Todo, user: User, perm: PermissionType):
    exists = any(p.user_id == user.id and p.permission == perm for p in todo.permissions)
    if not exists:
        perm_obj = TodoPermission(todo_id=todo.id, user_id=user.id, permission=perm)
        db.add(perm_obj)
        await db.commit()
        await db.refresh(perm_obj)
    return

async def revoke_permission(db: AsyncSession, todo: Todo, user: User, perm: PermissionType):
    await db.execute(
        delete(TodoPermission).where(
            TodoPermission.todo_id == todo.id,
            TodoPermission.user_id == user.id,
            TodoPermission.permission == perm
        )
    )
    await db.commit()