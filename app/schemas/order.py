from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]


class OrderStatusUpdate(BaseModel):
    status: str  # pending, processing, shipped, delivered, cancelled


class OrderOut(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    payment_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItemOut] = []

    class Config:
        from_attributes = True
