import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.booking import BookingStatus, PaymentStatus


class BookingCreate(BaseModel):
    center_id: uuid.UUID
    package_id: uuid.UUID
    scheduled_date: datetime


class BookingOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    center_id: uuid.UUID
    package_id: uuid.UUID
    scheduled_date: datetime
    status: BookingStatus
    payment_status: PaymentStatus
    razorpay_order_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RazorpayOrderOut(BaseModel):
    booking_id: uuid.UUID
    razorpay_order_id: str
    amount: int  # in paise
    currency: str = "INR"
    key_id: str


class PaymentVerifyRequest(BaseModel):
    booking_id: uuid.UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
