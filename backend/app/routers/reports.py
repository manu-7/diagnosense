import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.booking import Booking
from app.models.center import DiagnosticCenter
from app.models.package import Package
from app.models.report import Report
from app.models.user import User, UserRole
from app.schemas.report import GenerateReportRequest, ReportDownloadOut, ReportOut
from app.services import pdf_report_service, storage_service
from app.services.ai_service import flag_anomalies
from app.services.rag_service import explain_anomalies_rag
from app.tasks.tasks import extract_and_analyze_report, process_report_anomalies, send_report_ready_notification

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
logger = logging.getLogger(__name__)


async def _get_owned_center_id(current_user: User, db: AsyncSession) -> uuid.UUID:
    """Resolve the DiagnosticCenter row owned by this CENTER user. Used to enforce
    that a center account can only touch bookings/reports that belong to it -
    role alone (UserRole.CENTER) is not enough to prevent cross-center access."""
    result = await db.execute(select(DiagnosticCenter).where(DiagnosticCenter.user_id == current_user.id))
    center = result.scalar_one_or_none()
    if not center:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Center profile not found for this account")
    return center.id


@router.post("/{booking_id}/generate", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def generate_report(
    booking_id: uuid.UUID,
    payload: GenerateReportRequest,
    current_user: User = Depends(require_role(UserRole.CENTER)),
    db: AsyncSession = Depends(get_db),
):
    """Primary report path: the center types in the values it measured, and
    the system generates a clean, structured PDF from that data - instead of
    the center uploading their own scanned/handwritten file and hoping OCR
    can read it. There's nothing to misread here: the source of truth is
    already structured, so this works identically whether the center's
    internal notes were handwritten or typed - only the clean digital
    values ever reach this endpoint.

    Anomaly detection is still the same deterministic rule-based check
    against clinical reference ranges (see ai_service.NORMAL_RANGES) - the
    AI here only phrases the explanation of already-decided anomalies, and
    is never used to produce the numbers themselves."""
    owned_center_id = await _get_owned_center_id(current_user, db)

    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking or booking.center_id != owned_center_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    patient = (await db.execute(select(User).where(User.id == booking.patient_id))).scalar_one_or_none()
    center = (await db.execute(select(DiagnosticCenter).where(DiagnosticCenter.id == booking.center_id))).scalar_one_or_none()
    package = (await db.execute(select(Package).where(Package.id == booking.package_id))).scalar_one_or_none()
    if not patient or not center or not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking is missing linked records")

    extracted_values = payload.extracted_values
    anomalies = flag_anomalies(extracted_values)
    ai_explanation, explanation_sources = await explain_anomalies_rag(anomalies, db)

    try:
        pdf_bytes = pdf_report_service.generate_report_pdf(
            patient_name=patient.name,
            center_name=center.center_name,
            package_name=package.name,
            scheduled_date=booking.scheduled_date,
            extracted_values=extracted_values,
            anomalies=anomalies,
            ai_explanation=ai_explanation,
            explanation_sources=explanation_sources,
        )
    except Exception:
        logger.error("PDF generation failed for booking %s", booking_id, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate the report PDF")

    key = storage_service.build_object_key(booking_id, "diagnostic_report.pdf")
    try:
        storage_service.upload_file(pdf_bytes, key, content_type="application/pdf")
    except Exception:
        logger.error("S3 upload failed for generated report, booking %s", booking_id, exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Report storage is temporarily unavailable")

    # One report per booking - update if the center is re-generating (e.g. a
    # correction), otherwise create the row for the first time.
    existing = await db.execute(select(Report).where(Report.booking_id == booking_id))
    report = existing.scalar_one_or_none()
    if report:
        report.file_key = key
        report.original_filename = "diagnostic_report.pdf"
        report.extracted_values = extracted_values
        report.anomalies = anomalies
        report.ai_explanation = ai_explanation
        report.explanation_sources = explanation_sources
    else:
        report = Report(
            booking_id=booking_id,
            file_key=key,
            original_filename="diagnostic_report.pdf",
            extracted_values=extracted_values,
            anomalies=anomalies,
            ai_explanation=ai_explanation,
            explanation_sources=explanation_sources,
        )
        db.add(report)

    await db.commit()
    await db.refresh(report)

    try:
        send_report_ready_notification.delay(patient.email, patient.name)
    except Exception:
        logger.error("Failed to enqueue report-ready notification for report %s", report.id, exc_info=True)

    return report


@router.post("/{booking_id}/upload", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def upload_report(
    booking_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.CENTER)),
    db: AsyncSession = Depends(get_db),
):
    """Legacy/alternate path: center uploads its own file (e.g. a scanned
    original for record-keeping) instead of using POST /generate. OCR-based
    auto-extraction is best-effort and does not reliably handle handwriting -
    prefer /generate for anything the center can type in directly."""
    owned_center_id = await _get_owned_center_id(current_user, db)

    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.center_id != owned_center_id:
        # Booking exists but belongs to a different center - 404 rather than 403
        # so we don't leak booking existence to centers that shouldn't see it.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    file_bytes = await file.read()
    key = storage_service.build_object_key(booking_id, file.filename)
    try:
        storage_service.upload_file(file_bytes, key, content_type=file.content_type or "application/octet-stream")
    except Exception:
        logger.error("S3 upload failed for booking %s", booking_id, exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Report storage is temporarily unavailable")

    report = Report(booking_id=booking_id, file_key=key, original_filename=file.filename)
    db.add(report)
    await db.commit()
    await db.refresh(report)

    patient_result = await db.execute(select(User).where(User.id == booking.patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient:
        try:
            send_report_ready_notification.delay(patient.email, patient.name)
        except Exception:
            logger.error("Failed to enqueue report-ready notification for report %s", report.id, exc_info=True)

    try:
        # Best-effort: tries to auto-extract lab values via OCR + LLM parsing so
        # the center doesn't have to manually retype every value. If nothing
        # usable is found (bad scan, unusual layout), the report is simply left
        # for POST /reports/{id}/analyze - this never blocks or fails the upload.
        extract_and_analyze_report.delay(str(report.id), key, file.content_type or "application/octet-stream")
    except Exception:
        logger.error("Failed to enqueue auto-extraction for report %s", report.id, exc_info=True)

    return report


@router.post("/{report_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_report(
    report_id: uuid.UUID,
    extracted_values: dict,
    current_user: User = Depends(require_role(UserRole.CENTER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Manual override for anomaly analysis - kicks off async detection (Celery)
    so the request returns instantly. extracted_values e.g.
    {"hemoglobin": 10.2, "wbc": 12500}. Most reports are now auto-analyzed via
    OCR right after upload (see extract_and_analyze_report); this endpoint stays
    available for reports where auto-extraction found nothing usable, or to
    correct values by hand."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if current_user.role == UserRole.CENTER:
        owned_center_id = await _get_owned_center_id(current_user, db)
        booking_result = await db.execute(select(Booking).where(Booking.id == report.booking_id))
        booking = booking_result.scalar_one_or_none()
        if not booking or booking.center_id != owned_center_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report.extracted_values = extracted_values
    await db.commit()

    try:
        task = process_report_anomalies.delay(str(report_id), extracted_values)
        task_id = task.id
    except Exception:
        logger.error("Failed to enqueue anomaly analysis for report %s", report_id, exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Analysis queue is temporarily unavailable")

    return {"task_id": task_id, "status": "processing"}


def _owns_report(current_user: User, booking: Booking) -> bool:
    return current_user.role == UserRole.ADMIN or booking.patient_id == current_user.id


@router.get("/by-booking/{booking_id}", response_model=ReportOut)
async def get_report_by_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lets a patient (or the owning center/admin) look up the report for a
    booking without already knowing the report_id - needed for the frontend's
    booking to report detail navigation."""
    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    authorized = _owns_report(current_user, booking)
    if not authorized and current_user.role == UserRole.CENTER:
        owned_center_id = await _get_owned_center_id(current_user, db)
        authorized = booking.center_id == owned_center_id
    if not authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this report")

    report_result = await db.execute(select(Report).where(Report.booking_id == booking_id))
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No report uploaded for this booking yet")
    return report


@router.get("/{report_id}/download", response_model=ReportDownloadOut)
async def download_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    booking_result = await db.execute(select(Booking).where(Booking.id == report.booking_id))
    booking = booking_result.scalar_one_or_none()

    if not booking or not _owns_report(current_user, booking):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this report")

    signed_url = storage_service.generate_signed_url(report.file_key)
    return ReportDownloadOut(signed_url=signed_url, expires_in_seconds=300)
