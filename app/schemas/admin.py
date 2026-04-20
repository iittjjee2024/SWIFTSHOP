from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.user import UserOut


class AdminCreate(BaseModel):
    user_id:     int
    admin_level: Optional[int] = 1
    department:  Optional[str] = None
    notes:       Optional[str] = None


class AdminUpdate(BaseModel):
    admin_level: Optional[int] = None
    department:  Optional[str] = None
    notes:       Optional[str] = None
    is_active:   Optional[bool] = None


class AdminOut(BaseModel):
    id:            int
    user_id:       int
    admin_level:   int
    department:    Optional[str] = None
    notes:         Optional[str] = None
    is_active:     bool
    created_at:    datetime
    updated_at:    Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    user:          Optional[UserOut] = None

    class Config:
        from_attributes = True
