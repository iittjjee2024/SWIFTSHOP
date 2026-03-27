from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import httpx
import razorpay
from app import models
from app.config import (
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET,
    RAZORPAY_WEBHOOK_SECRET
)

class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.razorpay_client = razorpay.Client(
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
        )
    
    async def process_payment(
        self, 
        order_id: int, 
        payment_method: str, 
        payment_data: Dict[str, Any]
    ) -> models.Payment:
        """Process payment for an order"""
        
        order = self.db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        if order.payment_status == "paid":
            raise ValueError("Order already paid")
        payment = models.Payment(
            order_id=order_id,
            amount=order.total_amount,
            payment_method=payment_method,
            status="processing",
            transaction_id=self._generate_transaction_id()
        )
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        try:
            # Process payment based on method
            if payment_method == "razorpay":
                success = await self._process_razorpay_payment(payment, payment_data)
            elif payment_method == "cod":  # Cash on delivery
                success = self._process_cod_payment(payment)
            else:
                raise ValueError(f"Unsupported payment method: {payment_method}")
            
            if success:
                payment.status = "completed"
                order.payment_status = "paid"
                order.status = "processing"  
            else:
                payment.status = "failed"
            
        except Exception as e:
            payment.status = "failed"
            print(f"Payment processing error: {e}")
        
        self.db.commit()
        return payment
    
    async def refund_payment(self, payment_id: int, amount: Optional[float] = None) -> bool:
        """Process refund for a payment"""
        
        payment = self.db.query(models.Payment).filter(models.Payment.id == payment_id).first()
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.status != "completed":
            raise ValueError("Can only refund completed payments")
        
        refund_amount = amount or payment.amount
        
        try:
            if payment.payment_method == "razorpay":
                success = await self._process_razorpay_refund(payment, refund_amount)
            else:
                # For COD or other methods, just mark as refunded
                success = True
            
            if success:
                payment.status = "refunded"
                order = payment.order
                order.status = "cancelled"
                
                for item in order.items:
                    item.product.stock_quantity += item.quantity
                
                self.db.commit()
                return True
            
        except Exception as e:
            print(f"Refund processing error: {e}")
        
        return False
    
    def get_payment_status(self, payment_id: int) -> Optional[models.Payment]:
        """Get payment status"""
        return self.db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    
    def create_razorpay_order(self, order_id: int) -> Dict[str, Any]:
        """Create Razorpay order for payment"""
        order = self.db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        # Create Razorpay order
        order_data = {
            "amount": int(order.total_amount * 100),  # Amount in paisa
            "currency": "INR",
            "receipt": f"order_{order_id}",
            "notes": {
                "order_id": str(order_id),
                "user_id": str(order.user_id)
            }
        }
        
        razorpay_order = self.razorpay_client.order.create(order_data)
        return razorpay_order
    
    def verify_razorpay_webhook(self, webhook_body: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            self.razorpay_client.utility.verify_webhook_signature(
                webhook_body.decode(),
                signature,
                RAZORPAY_WEBHOOK_SECRET
            )
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
    
    async def handle_razorpay_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Handle Razorpay webhook events"""
        event = webhook_data.get("event")
        payment_entity = webhook_data.get("payload", {}).get("payment", {}).get("entity", {})
        
        if event == "payment.captured":
            # Payment was successfully captured
            razorpay_payment_id = payment_entity.get("id")
            
            # Find our payment record
            payment = self.db.query(models.Payment).filter(
                models.Payment.transaction_id == razorpay_payment_id
            ).first()
            
            if payment and payment.status != "completed":
                payment.status = "completed"
                order = payment.order
                order.payment_status = "paid"
                order.status = "processing"
                self.db.commit()
                return True
        
        return False
    
    async def _process_razorpay_payment(self, payment: models.Payment, payment_data: Dict[str, Any]) -> bool:
        """Process Razorpay payment"""
        try:
            # Verify payment signature
            razorpay_payment_id = payment_data.get("razorpay_payment_id")
            razorpay_order_id = payment_data.get("razorpay_order_id")
            razorpay_signature = payment_data.get("razorpay_signature")

            if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
                return False

            # Verify payment signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            self.razorpay_client.utility.verify_payment_signature(params_dict)

            # Fetch payment details from Razorpay
            payment_details = self.razorpay_client.payment.fetch(razorpay_payment_id)

            # Check if payment was successful
            if payment_details.get("status") == "captured":
                # Update transaction ID with Razorpay payment ID
                payment.transaction_id = razorpay_payment_id
                return True

            return False

        except razorpay.errors.SignatureVerificationError:
            print("Razorpay signature verification failed")
            return False
        except Exception as e:
            print(f"Razorpay payment error: {e}")
            return False

    async def _process_paypal_payment(self, payment: models.Payment, payment_data: Dict[str, Any]) -> bool:
        """Process PayPal payment"""
        try:
            return payment_data.get("mock_success", True)
        except Exception as e:
            print(f"PayPal payment error: {e}")
            return False

    def _process_cod_payment(self, payment: models.Payment) -> bool:
        """Process Cash on Delivery"""
        return True

    async def _process_razorpay_refund(self, payment: models.Payment, amount: float) -> bool:
        """Process Razorpay refund"""
        try:
            # Create refund
            refund_data = {
                "payment_id": payment.transaction_id,
                "amount": int(amount * 100),  # Convert to paisa
            }

            refund = self.razorpay_client.payment.refund(payment.transaction_id, refund_data)
            return refund.get("status") == "processed"

        except Exception as e:
            print(f"Razorpay refund error: {e}")
            return False

    async def _process_paypal_refund(self, payment: models.Payment, amount: float) -> bool:
        """Process PayPal refund"""
        return True
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"txn_{uuid.uuid4().hex[:16]}"

async def process_order_payment(db: Session, order_id: int, payment_method: str, payment_data: Dict[str, Any]):
    """Process payment for an order"""
    service = PaymentService(db)
    return await service.process_payment(order_id, payment_method, payment_data)

async def refund_order_payment(db: Session, payment_id: int, amount: Optional[float] = None):
    """Refund a payment"""
    service = PaymentService(db)
    return await service.refund_payment(payment_id, amount)
