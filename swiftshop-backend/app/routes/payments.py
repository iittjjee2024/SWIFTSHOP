from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.services.payment_service import PaymentService
from app.utils.security import get_current_user
from app import models

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)

@router.post("/razorpay/order/{order_id}")
async def create_razorpay_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create Razorpay order for payment"""
    try:
        service = PaymentService(db)
        order_data = service.create_razorpay_order(order_id)
        return {
            "order_id": order_data["id"],
            "amount": order_data["amount"],
            "currency": order_data["currency"],
            "key": service.razorpay_client.auth[0]  # Razorpay Key ID
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/razorpay/verify")
async def verify_razorpay_payment(
    payment_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Verify and process Razorpay payment"""
    try:
        service = PaymentService(db)
        payment = await service.process_payment(
            order_id=payment_data["order_id"],
            payment_method="razorpay",
            payment_data=payment_data
        )
        return {"status": "success", "payment_id": payment.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Razorpay webhook"""
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature")

        service = PaymentService(db)

        # Verify webhook signature
        if not service.verify_razorpay_webhook(body, signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Parse webhook data
        import json
        webhook_data = json.loads(body.decode())

        # Handle webhook
        success = await service.handle_razorpay_webhook(webhook_data)

        if success:
            return {"status": "ok"}
        else:
            raise HTTPException(status_code=400, detail="Webhook processing failed")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{payment_id}")
def get_payment_status(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get payment status"""
    service = PaymentService(db)
    payment = service.get_payment_status(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Check if user owns this payment
    if payment.order.user.email != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "transaction_id": payment.transaction_id,
        "created_at": payment.created_at
    }

@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: int,
    refund_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Refund a payment"""
    service = PaymentService(db)
    payment = service.get_payment_status(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Check if user owns this payment (or is admin)
    if payment.order.user.email != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")

    amount = refund_data.get("amount") if refund_data else None

    success = await service.refund_payment(payment_id, amount)

    if success:
        return {"status": "refunded"}
    else:
        raise HTTPException(status_code=400, detail="Refund failed")