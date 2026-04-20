import hmac
import hashlib
import razorpay
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Payment, Order
from app.schemas.payment import PaymentCreate, RazorpayVerify
from app.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET


def get_razorpay_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay credentials not configured")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def initiate_payment(db: Session, data: PaymentCreate, user_id: int) -> dict:
    order = db.query(Order).filter(Order.id == data.order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Order already paid")

    if data.payment_method == "cod":
        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            payment_method="cod",
            transaction_id=f"COD-{order.id}",
            status="pending",
        )
        db.add(payment)
        order.payment_status = "pending"
        order.status = "processing"
        db.commit()
        db.refresh(payment)
        return {"payment_method": "cod", "message": "COD order confirmed", "order_id": order.id}

    # Razorpay
    client = get_razorpay_client()
    amount_paise = int(order.total_amount * 100)
    razorpay_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"order_{order.id}",
    })
    return {
        "razorpay_order_id": razorpay_order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID,
        "order_id": order.id,
    }


def verify_razorpay_payment(db: Session, data: RazorpayVerify, user_id: int) -> dict:
    # Verify signature
    body = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(), body.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, data.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Find the order by razorpay order receipt
    client = get_razorpay_client()
    rz_order = client.order.fetch(data.razorpay_order_id)
    order_id = int(rz_order["receipt"].replace("order_", ""))
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_method="razorpay",
        transaction_id=data.razorpay_payment_id,
        status="completed",
    )
    db.add(payment)
    order.payment_status = "paid"
    order.status = "processing"
    db.commit()
    return {"message": "Payment verified successfully", "order_id": order.id}
