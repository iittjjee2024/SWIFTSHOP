from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app import models
from app.utils.security import get_current_user

router = APIRouter(prefix="/admin")

def verify_admin(email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify that the current user is an admin"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user

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

@router.post("/query")
def execute_query(query_request: dict, admin: models.User = Depends(verify_admin), db: Session = Depends(get_db)):
    """Execute a SQL query (admin only). Supports SELECT, INSERT, UPDATE, DELETE with restrictions."""
    query = query_request.get("query", "").strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Security: Validate query type
    query_upper = query.upper()
    allowed_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "JOIN", "LEFT", 
                        "INNER", "ORDER", "BY", "LIMIT", "GROUP", "HAVING", "AND", "OR", "DISTINCT"]
    
    # Check for dangerous keywords
    dangerous_keywords = ["DROP", "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise HTTPException(status_code=400, detail=f"Operation '{keyword}' not allowed")
    
    # Ensure at least one allowed keyword is present
    if not any(kw in query_upper for kw in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
        raise HTTPException(status_code=400, detail="Query must be a SELECT, INSERT, UPDATE, or DELETE statement")
    
    try:
        # Execute the query
        result = db.execute(text(query))
        db.commit()
        
        # Format results
        if query_upper.startswith("SELECT"):
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            return {
                "status": "success",
                "rows_affected": len(data),
                "columns": list(columns),
                "data": data
            }
        else:
            # For INSERT, UPDATE, DELETE
            return {
                "status": "success",
                "rows_affected": result.rowcount,
                "message": f"{result.rowcount} rows affected"
            }
    
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error": str(e),
            "message": "Query execution failed"
        }
    finally:
        db.close()
