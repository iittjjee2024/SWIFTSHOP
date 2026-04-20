from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.payment import PaymentCreate, RazorpayVerify, PaymentOut
from app.services import payment as payment_service
from app.services.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate")
def initiate_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return payment_service.initiate_payment(db, data, current_user.id)


@router.post("/verify")
def verify_payment(
    data: RazorpayVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return payment_service.verify_razorpay_payment(db, data, current_user.id)

