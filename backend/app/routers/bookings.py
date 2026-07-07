import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.center import DiagnosticCenter
from app.models.package import Package
from app.models.user import User, UserRole
from app.schemas.booking import BookingCreate, BookingOut, PaymentVerifyRequest, RazorpayOrderOut
from app.services import payment_service
from app.tasks.tasks import send_booking_confirmation

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])
logger = logging.getLogger(__name__)


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db),
):
    package_result = await db.execute(
        select(Package).where(Package.id == payload.package_id, Package.center_id == payload.center_id)
    )
    package = package_result.scalar_one_or_none()
    if not package or not package.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found for this center")

    booking = Booking(
        patient_id=current_user.id,
        center_id=payload.center_id,
        package_id=payload.package_id,
        scheduled_date=payload.scheduled_date,
        status=BookingStatus.PENDING_PAYMENT,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@router.post("/{booking_id}/create-order", response_model=RazorpayOrderOut)
async def create_payment_order(
    booking_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.patient_id == current_user.id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking already paid")

    package_result = await db.execute(select(Package).where(Package.id == booking.package_id))
    package = package_result.scalar_one_or_none()

    order = payment_service.create_order(amount_rupees=float(package.price), receipt=str(booking.id))
    booking.razorpay_order_id = order["id"]
    await db.commit()

    return RazorpayOrderOut(
        booking_id=booking.id,
        razorpay_order_id=order["id"],
        amount=order["amount"],
        key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/verify-payment", response_model=BookingOut)
async def verify_payment(
    payload: PaymentVerifyRequest,
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(Booking.id == payload.booking_id, Booking.patient_id == current_user.id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.razorpay_order_id != payload.razorpay_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID mismatch")

    is_valid = payment_service.verify_payment_signature(
        payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature
    )
    if not is_valid:
        booking.payment_status = PaymentStatus.FAILED
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment signature verification failed")

    booking.payment_status = PaymentStatus.PAID
    booking.status = BookingStatus.CONFIRMED
    booking.razorpay_payment_id = payload.razorpay_payment_id
    booking.razorpay_signature = payload.razorpay_signature
    await db.commit()
    await db.refresh(booking)

    center_result = await db.execute(select(DiagnosticCenter).where(DiagnosticCenter.id == booking.center_id))
    center = center_result.scalar_one_or_none()
    # Payment is already verified and committed above - a broker/Celery outage here
    # should never turn a successful payment into an error response to the patient.
    try:
        send_booking_confirmation.delay(
            current_user.email, current_user.name, center.center_name if center else "the center",
            booking.scheduled_date.isoformat(),
        )
    except Exception:
        logger.error("Failed to enqueue booking confirmation email for booking %s", booking.id, exc_info=True)
    return booking


@router.get("/me", response_model=list[BookingOut])
async def my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.patient_id == current_user.id))
    return result.scalars().all()


@router.get("/center", response_model=list[BookingOut])
async def center_bookings(
    current_user: User = Depends(require_role(UserRole.CENTER)),
    db: AsyncSession = Depends(get_db),
):
    """Bookings placed at the diagnostic center owned by the current CENTER
    account, scoped by ownership not just role, same pattern as reports.py."""
    center_result = await db.execute(select(DiagnosticCenter).where(DiagnosticCenter.user_id == current_user.id))
    center = center_result.scalar_one_or_none()
    if not center:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Create a center profile first")

    result = await db.execute(
        select(Booking).where(Booking.center_id == center.id, Booking.payment_status == PaymentStatus.PAID)
    )
    return result.scalars().all()
