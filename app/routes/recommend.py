from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.product import ProductOut
from app.services.recommend import get_recommendations

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.get("/", response_model=List[ProductOut])
def recommend_products(
    category: Optional[str] = Query(None),
    limit: int = Query(8, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return get_recommendations(db, category, limit)

