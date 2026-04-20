from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Order, Product
from app.models.order import OrderItem
from app.schemas.order import OrderCreate, OrderStatusUpdate
from typing import List


def create_order(db: Session, data: OrderCreate, user_id: int) -> Order:
    total = 0.0
    items_data = []

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id, Product.is_active == True).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for '{product.name}'")
        total += product.price * item.quantity
        items_data.append((product, item.quantity))

    order = Order(user_id=user_id, total_amount=total, status="pending", payment_status="pending")
    db.add(order)
    db.flush()

    for product, qty in items_data:
        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=qty, price=product.price)
        db.add(order_item)
        product.stock_quantity -= qty

    db.commit()
    db.refresh(order)
    return order


def get_user_orders(db: Session, user_id: int) -> List[Order]:
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()


def get_order_by_id(db: Session, order_id: int, user_id: int = None) -> Order:
    query = db.query(Order).filter(Order.id == order_id)
    if user_id:
        query = query.filter(Order.user_id == user_id)
    order = query.first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def update_order_status(db: Session, order_id: int, data: OrderStatusUpdate) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    valid = ["pending", "processing", "shipped", "delivered", "cancelled"]
    if data.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order
