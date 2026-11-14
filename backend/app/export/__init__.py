"""PDF export for a user-reviewed Ticky draft."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Draft


def render_pdf(draft: Draft) -> bytes:
    """Render the current draft and attachment checklist. Does not fetch or attach files."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=0.72 * inch, leftMargin=0.72 * inch,
        topMargin=0.68 * inch, bottomMargin=0.68 * inch,
        title="Ticky — Draft for Review", author="Ticky",
    )
    base = getSampleStyleSheet()
    title = ParagraphStyle("TC_Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=17, leading=21, alignment=TA_LEFT, textColor=colors.HexColor("#172554"), spaceAfter=8)
    body = ParagraphStyle("TC_Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, spaceAfter=7, wordWrap="CJK")
    small = ParagraphStyle("TC_Small", parent=body, fontSize=8, leading=11, textColor=colors.HexColor("#475569"))
    heading = ParagraphStyle("TC_Heading", parent=base["Heading2"], fontSize=11, leading=14, textColor=colors.HexColor("#1e3a8a"), spaceBefore=9, spaceAfter=5)

    story = [
        Paragraph("Ticky — Draft for Review", title),
        Paragraph("IMPORTANT: Review every statement for accuracy. This document is a draft only; it is not legal advice and has not been submitted.", small),
        Spacer(1, 10),
        Paragraph("Statement", heading),
    ]
    for paragraph in draft.text.split("\n\n"):
        safe = escape(paragraph).replace("\n", "<br/>")
        story.append(Paragraph(safe, body))

    story.append(Paragraph("Evidence checklist", heading))
    if draft.attachments:
        rows = [[Paragraph("File", small), Paragraph("Document ID", small)]]
        for item in draft.attachments:
            rows.append([Paragraph(escape(item.filename), body), Paragraph(escape(str(item.document_id)), small)])
        table = Table(rows, colWidths=[2.2 * inch, 4.5 * inch], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        story.append(Paragraph("The source files are not embedded in this PDF. Attach copies separately when submitting.", small))
    else:
        story.append(Paragraph("No evidence files are listed.", body))

    story.append(Paragraph("Official submission instructions", heading))
    for step in draft.submission_steps:
        story.append(KeepTogether([
            Paragraph(escape(step.text), body),
            Paragraph(f'<link href="{escape(step.url)}" color="#1d4ed8">{escape(step.url)}</link>', small),
        ]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Prepared by Ticky for user review. Verify the current instructions and deadline with the agency or court named on your notice.", small))
    doc.build(story)
    return buffer.getvalue()
