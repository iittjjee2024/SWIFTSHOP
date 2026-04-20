from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models import User, Order, Product, Admin
from app.schemas.user import UserOut
from app.schemas.order import OrderOut
from app.schemas.admin import AdminCreate, AdminUpdate, AdminOut
from app.services.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── SQL Query Tool ────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str

# Blocked keywords to prevent destructive operations
BLOCKED = ["drop", "truncate", "alter", "create", "pg_", "information_schema"]

@router.post("/query")
def run_query(
    body: QueryRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Execute a raw SQL query (admin only). SELECT returns rows; INSERT/UPDATE/DELETE returns affected count."""
    q = body.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    q_lower = q.lower()
    for blocked in BLOCKED:
        if blocked in q_lower:
            return {"status": "error", "error": f"'{blocked.upper()}' statements are not allowed"}

    try:
        result = db.execute(text(q))
        db.commit()

        if q_lower.startswith("select"):
            rows_raw = result.fetchall()
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in rows_raw]
            return {
                "status": "success",
                "columns": columns,
                "data": rows,
                "rows_affected": len(rows),
            }
        else:
            return {
                "status": "success",
                "message": f"Query executed successfully. {result.rowcount} row(s) affected.",
                "rows_affected": result.rowcount,
            }
    except Exception as e:
        db.rollback()
        return {"status": "error", "error": str(e)}


# ── Admin Table CRUD ──────────────────────────────────────────

@router.post("/admins", response_model=AdminOut, status_code=201)
def create_admin(
    data: AdminCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Promote a user to admin — creates a record in the admins table."""
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if db.query(Admin).filter(Admin.user_id == data.user_id).first():
        raise HTTPException(status_code=400, detail="User is already an admin")
    admin = Admin(**data.model_dump())
    user.is_admin = True
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.get("/admins", response_model=List[AdminOut])
def list_admins(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List all admin records with their linked user info."""
    return db.query(Admin).offset(skip).limit(limit).all()


@router.get("/admins/{admin_id}", response_model=AdminOut)
def get_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


@router.put("/admins/{admin_id}", response_model=AdminOut)
def update_admin(
    admin_id: int,
    data: AdminUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Update admin level, department, notes, or active status."""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(admin, field, value)
    # Sync is_active back to users table
    if data.is_active is not None:
        admin.user.is_admin = data.is_active
    db.commit()
    db.refresh(admin)
    return admin


@router.delete("/admins/{admin_id}")
def revoke_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Revoke admin access — removes from admins table and unsets is_admin on user."""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    admin.user.is_admin = False
    db.delete(admin)
    db.commit()
    return {"message": f"Admin access revoked for user_id {admin.user_id}"}


# ── User Management ───────────────────────────────────────────

@router.get("/users", response_model=List[UserOut])
def list_all_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return db.query(User).offset(skip).limit(limit).all()


@router.patch("/users/{user_id}/toggle-active", response_model=UserOut)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


# ── Order Management ──────────────────────────────────────────

@router.get("/orders", response_model=List[OrderOut])
def list_all_orders(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return db.query(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


# ── Dashboard Stats ───────────────────────────────────────────

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    total_users     = db.query(User).count()
    total_admins    = db.query(Admin).filter(Admin.is_active == True).count()
    total_products  = db.query(Product).filter(Product.is_active == True).count()
    total_orders    = db.query(Order).count()
    total_revenue   = db.query(func.sum(Order.total_amount)).filter(Order.payment_status == "paid").scalar() or 0.0
    pending_orders  = db.query(Order).filter(Order.status == "pending").count()
    return {
        "total_users":     total_users,
        "total_admins":    total_admins,
        "total_products":  total_products,
        "total_orders":    total_orders,
        "total_revenue":   round(total_revenue, 2),
        "pending_orders":  pending_orders,
    }
