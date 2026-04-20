from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Product, Order
from app.models.order import OrderItem
from typing import List


def get_recommendations(db: Session, category: str = None, limit: int = 8) -> List[Product]:
    """Return top products by popularity (most ordered), optionally filtered by category."""
    popular_ids = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity).label("total"))
        .group_by(OrderItem.product_id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(50)
        .all()
    )
    popular_id_list = [p.product_id for p in popular_ids]

    query = db.query(Product).filter(Product.is_active == True)
    if category:
        query = query.filter(Product.category == category)

    if popular_id_list:
        # Return popular ones first, then fill with newest
        popular = query.filter(Product.id.in_(popular_id_list)).limit(limit).all()
        if len(popular) < limit:
            rest = (
                query.filter(Product.id.notin_(popular_id_list))
                .order_by(Product.created_at.desc())
                .limit(limit - len(popular))
                .all()
            )
            return popular + rest
        return popular

    return query.order_by(Product.created_at.desc()).limit(limit).all()
