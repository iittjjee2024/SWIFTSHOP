from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from app.services import order as order_service
from app.services.auth import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.create_order(db, data, current_user.id)


@router.get("/", response_model=List[OrderOut])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.get_user_orders(db, current_user.id)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admins can view any order; users only their own
    uid = None if current_user.is_admin else current_user.id
    return order_service.get_order_by_id(db, order_id, uid)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return order_service.update_order_status(db, order_id, data)

