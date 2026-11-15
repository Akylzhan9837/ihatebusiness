from collections.abc import Callable
from datetime import datetime, timedelta

from app.api.errors import ApiError
from app.models import Analysis, Answers, Case, Document, TicketFields
from app.services.analysis.citations import analyze_citation


RuleEvaluator = Callable[[TicketFields, Answers, list[Document]], Analysis]
ROUTING_FIELDS = {"city": "City", "issuing_authority": "Issuing authority", "violation_code": "Violation code"}
REQUIRED_FIELDS = {
    **ROUTING_FIELDS, "ticket_number": "Ticket number", "issue_date": "Issue date",
    "issue_time": "Issue time", "location": "Location", "plate_number": "Plate number",
    "plate_state": "Plate state",
}
NYC_NAMES = {"nyc", "new york city", "city of new york", "manhattan", "brooklyn", "queens", "bronx", "the bronx", "staten island"}
AUTHORITIES = {"nyc department of finance", "new york city department of finance", "department of finance nyc", "nyc dof"}


def matching_receipt(case: Case) -> Document | None:
    answers = case.answers
    fields = case.confirmed_fields
    if not (
        answers.payment_method == "parknyc" and answers.receipt_details_confirmed
        and answers.zone_matches_ticket_location and answers.session_zone
        and answers.session_start and answers.session_end
        and answers.session_plate_number and answers.session_plate_state
        and fields.plate_number and fields.plate_state and fields.issue_date and fields.issue_time
    ):
        return None
    ticket_time = datetime.fromisoformat(f"{fields.issue_date}T{fields.issue_time}")
    start = datetime.fromisoformat(answers.session_start)
    end = datetime.fromisoformat(answers.session_end)
    ticket_plate = fields.plate_number.replace(" ", "").replace("-", "").upper()
    receipt_plate = answers.session_plate_number.replace(" ", "").replace("-", "").upper()
    if not (ticket_plate == receipt_plate and fields.plate_state.upper() == answers.session_plate_state.upper()
            and start - timedelta(minutes=5) <= ticket_time <= end + timedelta(minutes=5)):
        return None
    return next((doc for doc in case.documents
                 if doc.kind == "evidence" and doc.document_id == answers.evidence_document_id), None)


def analyze(case: Case, evaluate: RuleEvaluator | None) -> Analysis:
    fields = case.confirmed_fields
    city = fields.city.casefold() if fields.city else None
    authority = fields.issuing_authority.casefold() if fields.issuing_authority else None
    if fields.jurisdiction_state or fields.ticket_type:
        parknyc = (
            fields.jurisdiction_state == "NY" and fields.ticket_type == "parking"
            and city in NYC_NAMES and authority in AUTHORITIES
            and fields.violation_code is not None and fields.violation_code.lstrip("0") == "38"
        )
        if not parknyc:
            return analyze_citation(case, is_nyc=city in NYC_NAMES, is_dof=authority in AUTHORITIES)
        if not fields.ticket_number or len(fields.ticket_number) != 10 or not fields.ticket_number.isascii() or not fields.ticket_number.isdigit():
            return Analysis(status="needs_information", summary="Enter the 10-digit NYC ticket number.", missing_information=["NYC ticket number"])
    if ((city and city not in NYC_NAMES) or
        (authority and authority not in AUTHORITIES and authority != "department of finance") or
        (fields.violation_code and fields.violation_code.lstrip("0") != "38")):
        return Analysis(
            status="unsupported",
            summary="TicketClear covers NYC Department of Finance violation code 38 with ParkNYC payment.",
            next_steps=["Check the dispute instructions from the agency listed on your ticket."],
        )
    missing = [label for name, label in REQUIRED_FIELDS.items() if getattr(fields, name) is None]
    if missing:
        return Analysis(
            status="needs_information",
            summary="Verify the ticket details before evaluating the parking payment.",
            missing_information=missing,
            next_steps=["Return to ticket details and confirm the fields you can read."],
        )
    if evaluate is None:
        raise ApiError(503, "rules_unavailable", "Case review is temporarily unavailable. Try again later.", retryable=True)
    result = evaluate(fields, case.answers, case.documents)
    if result.status == "ready_for_draft" and not matching_receipt(case):
        raise ApiError(503, "rules_unavailable", "Case review could not verify the required information. Try again later.", retryable=True)
    source_ids = {source.id for source in result.sources}
    if any(not set(finding.source_ids) <= source_ids for finding in result.findings):
        raise ApiError(503, "rules_unavailable", "An official source could not be loaded. Try again later.", retryable=True)
    result.draft_available = result.status == "ready_for_draft"
    return result
