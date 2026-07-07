"""
Generates a clean, structured lab report PDF from values the diagnostic
center enters directly - rather than trusting OCR on a scanned/handwritten
file the center uploads. This sidesteps the handwriting-OCR problem
entirely: there is nothing to misread, because the source of truth is
already structured data, typed in by the center.

The AI in this flow still only does two things, same as everywhere else in
the project: it never decides what's medically abnormal (that's the fixed
NORMAL_RANGES table in ai_service.py) and it never invents a lab value -
it only phrases an explanation of numbers the center actually entered.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PINE = colors.HexColor("#0D4F45")
DANGER = colors.HexColor("#C0392B")
WARN = colors.HexColor("#B8862E")
MUTED = colors.HexColor("#63706A")


def generate_report_pdf(
    *,
    patient_name: str,
    center_name: str,
    package_name: str,
    scheduled_date: datetime,
    extracted_values: dict,
    anomalies: list[dict],
    ai_explanation: str,
    explanation_sources: list[dict] | None = None,
) -> bytes:
    """Returns the finished PDF as raw bytes, ready to upload to storage."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=2.2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], textColor=PINE, fontSize=20, spaceAfter=4)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"], textColor=MUTED, fontSize=10)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], textColor=PINE, spaceBefore=16, spaceAfter=8)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=15)
    disclaimer_style = ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=8.5, textColor=MUTED)

    anomaly_params = {a["parameter"] for a in anomalies}

    elements = [
        Paragraph("Diagnostic Test Report", title_style),
        Paragraph(f"{center_name}", meta_style),
        Spacer(1, 12),
        Table(
            [
                ["Patient", patient_name, "Test", package_name],
                ["Date", scheduled_date.strftime("%d %b %Y"), "Report generated", datetime.utcnow().strftime("%d %b %Y")],
            ],
            colWidths=[3 * cm, 5.7 * cm, 3 * cm, 5.7 * cm],
            style=TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                    ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#E5E3DD")),
                ]
            ),
        ),
        Spacer(1, 4),
        Paragraph("Test Results", section_style),
    ]

    table_data = [["Parameter", "Result", "Status"]]
    table_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E4EFEB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), PINE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E3DD")),
    ]
    for i, (param, value) in enumerate(extracted_values.items(), start=1):
        is_anomaly = param in anomaly_params
        status = "Normal"
        color = colors.HexColor("#1F8A5F")
        if is_anomaly:
            matched = next(a for a in anomalies if a["parameter"] == param)
            status = f"{matched['direction'].title()} range ({matched['severity']})"
            color = DANGER if matched["severity"] == "high" else WARN
        table_data.append([param.replace("_", " ").title(), str(value), status])
        table_styles.append(("TEXTCOLOR", (2, i), (2, i), color))

    elements.append(Table(table_data, colWidths=[6 * cm, 4 * cm, 7.4 * cm], style=TableStyle(table_styles)))

    if ai_explanation:
        elements.append(Paragraph("Summary", section_style))
        elements.append(Paragraph(ai_explanation, body_style))
        if explanation_sources:
            source_titles = ", ".join(sorted({s["source_title"] for s in explanation_sources}))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"Referenced material: {source_titles}", disclaimer_style))

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            "This report reflects values entered by the diagnostic center and automated reference-range "
            "checks. It is not a medical diagnosis. Please discuss these results with a licensed physician.",
            disclaimer_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()
