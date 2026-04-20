from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.services import product as product_service
from app.services.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[ProductOut])
def list_products(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return product_service.get_all_products(db, skip, limit, category, search)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return product_service.get_product_by_id(db, product_id)


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return product_service.create_product(db, data)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return product_service.update_product(db, product_id, data)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return product_service.delete_product(db, product_id)

