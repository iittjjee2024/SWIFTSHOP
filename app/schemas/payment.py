from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str  # razorpay, cod


class RazorpayVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
