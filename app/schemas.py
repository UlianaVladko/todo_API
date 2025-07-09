
from pydantic import BaseModel, constr
from typing import Optional, List
from enum import Enum

class PermissionType(str, Enum):
    read = "read"
    update = "update"

class UserCreate(BaseModel):
    username: str
    password: str

class UserShow(BaseModel):
    id: int
    username: str
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class TodoUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]

class TodoShow(BaseModel):
    id: int
    title: str
    description: str
    owner_id: int
    class Config:
        orm_mode = True

class PermissionGrantRequest(BaseModel):
    username: str
    permission: PermissionType