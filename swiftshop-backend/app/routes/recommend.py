from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"]
)

@router.get("/popular", response_model=List[schemas.Product])
def get_popular_products(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get most popular products based on order frequency"""
    popular_products = (
        db.query(models.Product)
        .join(models.OrderItem)
        .group_by(models.Product.id)
        .order_by(func.count(models.OrderItem.id).desc())
        .limit(limit)
        .all()
    )
    return popular_products

@router.get("/user/{user_id}", response_model=List[schemas.Product])
def get_personalized_recommendations(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get personalized recommendations based on user's order history"""
    user_orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    
    if not user_orders:
        return get_popular_products(limit, db)
    
    user_categories = set()
    for order in user_orders:
        for item in order.items:
            user_categories.add(item.product.category)
    
    purchased_product_ids = set()
    for order in user_orders:
        for item in order.items:
            purchased_product_ids.add(item.product_id)
    
    recommendations = (
        db.query(models.Product)
        .filter(models.Product.category.in_(user_categories))
        .filter(~models.Product.id.in_(purchased_product_ids))
        .order_by(func.random())  # Randomize for variety
        .limit(limit)
        .all()
    )
    
    return recommendations

@router.get("/similar/{product_id}", response_model=List[schemas.Product])
def get_similar_products(
    product_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get products similar to the given product"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    similar_products = (
        db.query(models.Product)
        .filter(models.Product.category == product.category)
        .filter(models.Product.id != product_id)
        .order_by(func.random())
        .limit(limit)
        .all()
    )
    
    return similar_products

@router.get("/trending", response_model=List[schemas.Product])
def get_trending_products(
    days: int = 7,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get trending products from recent orders"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    trending_products = (
        db.query(models.Product)
        .join(models.OrderItem)
        .join(models.Order)
        .filter(models.Order.created_at >= cutoff_date)
        .group_by(models.Product.id)
        .order_by(func.count(models.OrderItem.id).desc())
        .limit(limit)
        .all()
    )
    
    return trending_products