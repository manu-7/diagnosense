import hashlib
import hmac

import razorpay

from app.config import settings

_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_order(amount_rupees: float, receipt: str) -> dict:
    """Creates a Razorpay order. Amount must be converted to paise (smallest unit)."""
    amount_paise = int(round(amount_rupees * 100))
    order = _client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        }
    )
    return order


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verifies the Razorpay webhook/checkout signature using HMAC SHA256, exactly
    mirroring the check the server expects: hash of 'order_id|payment_id' signed
    with the key secret must equal the signature Razorpay sends back."""
    payload = f"{order_id}|{payment_id}"
    generated_signature = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode(),
        msg=payload.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(generated_signature, signature)
