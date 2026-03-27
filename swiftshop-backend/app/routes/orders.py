from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

@router.post("/", response_model=schemas.Order)
def create_order(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create a new order with items"""
    # Get current user
    user = db.query(models.User).filter(models.User.email == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate total amount and validate products
    total_amount = 0
    order_items = []
    
    for item_data in order_data.items:
        product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")
        if product.stock_quantity < item_data.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {product.name}")
        
        item_total = product.price * item_data.quantity
        total_amount += item_total
        
        order_items.append({
            "product_id": item_data.product_id,
            "quantity": item_data.quantity,
            "price": product.price
        })
    
    # Create order
    order = models.Order(
        user_id=user.id,
        total_amount=total_amount,
        status="pending",
        payment_status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Create order items
    for item_data in order_items:
        order_item = models.OrderItem(
            order_id=order.id,
            **item_data
        )
        db.add(order_item)
        
        # Update product stock
        product = db.query(models.Product).filter(models.Product.id == item_data["product_id"]).first()
        product.stock_quantity -= item_data["quantity"]
    
    db.commit()
    db.refresh(order)
    return order

@router.get("/", response_model=List[schemas.Order])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get user's orders"""
    user = db.query(models.User).filter(models.User.email == current_user).first()
    
    query = db.query(models.Order).filter(models.Order.user_id == user.id)
    
    if status:
        query = query.filter(models.Order.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    return orders

@router.get("/{order_id}", response_model=schemas.OrderDetail)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get a specific order with items"""
    user = db.query(models.User).filter(models.User.email == current_user).first()
    
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.user_id == user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@router.put("/{order_id}/status", response_model=schemas.Order)
def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update order status (user can cancel, admin can update any status)"""
    user = db.query(models.User).filter(models.User.email == current_user).first()
    
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Users can only cancel their own pending orders
    if not user.is_admin and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not user.is_admin and status_update.status != "cancelled":
        raise HTTPException(status_code=403, detail="Users can only cancel orders")
    
    if not user.is_admin and order.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending orders")
    
    order.status = status_update.status
    db.commit()
    db.refresh(order)
    return order

@router.get("/admin/all", response_model=List[schemas.Order])
def get_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get all orders (admin only)"""
    user = db.query(models.User).filter(models.User.email == current_user).first()
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(models.Order)
    
    if status:
        query = query.filter(models.Order.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    return orders

@router.delete("/{order_id}")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Cancel an order (user can cancel their own pending orders)"""
    user = db.query(models.User).filter(models.User.email == current_user).first()
    
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.user_id == user.id,
        models.Order.status == "pending"
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or cannot be cancelled")
    
    # Restore product stock
    for item in order.items:
        item.product.stock_quantity += item.quantity
    
    order.status = "cancelled"
    db.commit()
    
    return {"message": "Order cancelled successfully"}
