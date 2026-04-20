from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
