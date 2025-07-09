
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from .config import Base
import enum

class PermissionType(enum.Enum):
    read = "read"
    update = "update"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    todos = relationship("Todo", back_populates="owner")
    permissions = relationship("TodoPermission", back_populates="user")

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    owner = relationship("User", back_populates="todos")
    permissions = relationship("TodoPermission", back_populates="todo", cascade="all, delete-orphan")

class TodoPermission(Base):
    __tablename__ = "todo_permissions"
    id = Column(Integer, primary_key=True)
    todo_id = Column(Integer, ForeignKey("todos.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    permission = Column(Enum(PermissionType), nullable=False)
    __table_args__ = (UniqueConstraint("todo_id", "user_id", "permission"),)
    todo = relationship("Todo", back_populates="permissions")
    user = relationship("User", back_populates="permissions")