from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.utils.security import get_current_user

router = APIRouter(prefix="/admin")

@router.get("/stats/users")
def total_users(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return {"total_users": db.query(models.User).count()}
@router.get("/stats/products")
def total_products(db: Session = Depends(get_db)):
    return {"total_products": db.query(models.Product).count()}
@router.get("/stats/orders")
def total_orders(db: Session = Depends(get_db)):
    return {"total_orders": db.query(models.Order).count()}
@router.get("/stats/revenue")
def total_revenue(db: Session = Depends(get_db)):
    result = db.query(models.Order).all()
    total = sum([o.total_amount for o in result])
    return {"revenue": float(total)}
