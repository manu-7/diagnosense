import asyncio
import logging
import uuid

from app.database import AsyncSessionLocal
from app.models.report import Report
from app.services import storage_service
from app.services.ai_service import flag_anomalies
from app.services.email_service import send_email
from app.services.extraction_service import extract_lab_values_from_file
from app.services.rag_service import explain_anomalies_rag
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.send_booking_confirmation")
def send_booking_confirmation(patient_email: str, patient_name: str, center_name: str, scheduled_date: str) -> None:
    body = f"""
    <p>Hi {patient_name},</p>
    <p>Your diagnostic test at <b>{center_name}</b> is confirmed for <b>{scheduled_date}</b>.</p>
    <p>Please arrive 10 minutes early with a valid ID.</p>
    """
    send_email(patient_email, "Booking Confirmed - Diagnostic Test", body)


@celery_app.task(name="tasks.send_report_ready_notification")
def send_report_ready_notification(patient_email: str, patient_name: str) -> None:
    body = f"""
    <p>Hi {patient_name},</p>
    <p>Your diagnostic report is ready. Log in to your dashboard to view or download it.</p>
    """
    send_email(patient_email, "Your Diagnostic Report is Ready", body)


async def _analyze_and_persist(report_id: str, extracted_values: dict) -> dict:
    """Celery workers run outside the request's async session, so this opens
    its own short-lived one - both to run the RAG retrieval (needs a DB
    session to query reference_snippets) and to write the results back."""
    anomalies = flag_anomalies(extracted_values)
    async with AsyncSessionLocal() as db:
        explanation, sources = await explain_anomalies_rag(anomalies, db)

        report = await db.get(Report, uuid.UUID(report_id))
        if not report:
            logger.error("Report %s not found when persisting analysis results", report_id)
            return {"report_id": report_id, "anomalies": anomalies, "explanation": explanation}

        report.extracted_values = extracted_values
        report.anomalies = anomalies
        report.ai_explanation = explanation
        report.explanation_sources = sources
        await db.commit()

    return {"report_id": report_id, "anomalies": anomalies, "explanation": explanation, "sources": sources}


@celery_app.task(name="tasks.process_report_anomalies")
def process_report_anomalies(report_id: str, extracted_values: dict) -> dict:
    """Runs the rule-based anomaly check + RAG-grounded explanation asynchronously
    so the upload endpoint returns immediately instead of blocking on the AI call.
    Used for the manual-entry path (center already typed in extracted_values)."""
    return asyncio.run(_analyze_and_persist(report_id, extracted_values))


@celery_app.task(name="tasks.extract_and_analyze_report")
def extract_and_analyze_report(report_id: str, file_key: str, content_type: str) -> dict:
    """Auto path, runs right after upload: pulls the file back from storage,
    OCR/text-extracts it, parses lab values via LLM, then reuses the same
    rule-based anomaly + RAG-grounded explanation logic as the manual path. If
    extraction finds nothing usable, the report is simply left for the center
    to analyze manually via POST /reports/{id}/analyze - no error is raised."""
    try:
        file_bytes = storage_service.download_file(file_key)
    except Exception:
        logger.error("Failed to download report %s from storage for extraction", report_id, exc_info=True)
        return {"report_id": report_id, "status": "download_failed"}

    extracted_values = extract_lab_values_from_file(file_bytes, content_type)
    if not extracted_values:
        logger.info("No lab values auto-extracted for report %s; awaiting manual analysis.", report_id)
        return {"report_id": report_id, "status": "no_values_found"}

    result = asyncio.run(_analyze_and_persist(report_id, extracted_values))
    return {"report_id": report_id, "status": "analyzed", **result}


@celery_app.task(name="tasks.send_appointment_reminder")
def send_appointment_reminder(patient_email: str, patient_name: str, center_name: str, scheduled_date: str) -> None:
    body = f"""
    <p>Hi {patient_name},</p>
    <p>Reminder: your appointment at <b>{center_name}</b> is coming up on <b>{scheduled_date}</b>.</p>
    """
    send_email(patient_email, "Reminder: Upcoming Diagnostic Test", body)
