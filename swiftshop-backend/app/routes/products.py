from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_user

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

@router.post("/", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create a new product (admin only)"""
    # Check if user is admin (you'll need to implement this)
    # if not is_admin(current_user):
    #     raise HTTPException(status_code=403, detail="Not authorized")
    
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/", response_model=List[schemas.Product])
def get_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering"""
    query = db.query(models.Product)
    
    if category:
        query = query.filter(models.Product.category == category)
    
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    
    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update a product (admin only)"""
    # Check if user is admin
    # if not is_admin(current_user):
    #     raise HTTPException(status_code=403, detail="Not authorized")
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for field, value in product_update.dict(exclude_unset=True).items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Delete a product (admin only)"""
    # Check if user is admin
    # if not is_admin(current_user):
    #     raise HTTPException(status_code=403, detail="Not authorized")
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.get("/categories/", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """Get all unique product categories"""
    from sqlalchemy import distinct
    categories = db.query(distinct(models.Product.category)).all()
    return [cat[0] for cat in categories if cat[0]]

@router.get("/search/", response_model=List[schemas.Product])
def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search products by name or description"""
    products = (
        db.query(models.Product)
        .filter(
            (models.Product.name.ilike(f"%{q}%")) |
            (models.Product.description.ilike(f"%{q}%"))
        )
        .limit(limit)
        .all()
    )
    return products