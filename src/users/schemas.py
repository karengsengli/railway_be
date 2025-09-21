from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class UserBase(BaseModel):
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    roles: List[str] = []

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    limit: int


class UserRoleAssignment(BaseModel):
    user_id: int
    role_id: int


class UserRoleRemoval(BaseModel):
    user_id: int
    role_id: int