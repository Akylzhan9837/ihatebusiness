"""Conservative, evidence-led checks for the NYC DOF code 38 demo scenario.

This module does not decide whether a ticket is legally invalid. It checks whether
user-confirmed ParkNYC facts appear consistent enough to prepare a statement.
"""
from datetime import date, datetime, timedelta

from app.models import Analysis, Answers, Case, Document, Finding, Question, Source, TicketFields

ACCESS_DATE = date(2026, 11, 15)
DISPUTE_URL = "https://www.nyc.gov/site/finance/vehicles/dispute-a-ticket.page"
CODES_URL = "https://www.nyc.gov/site/finance/vehicles/services-violation-codes.page"
REQUIRED_SOURCE = Source(
    id="nyc-dof-dispute",
    title="Dispute a Ticket — NYC Department of Finance",
    url=DISPUTE_URL,
    jurisdiction="New York City",
    topic="Hearing process and filing deadline",
    accessed_at=ACCESS_DATE,
    relevant_excerpt=(
        "A hearing request should be made within 30 days after the ticket was issued "
        "to avoid late penalties. The Department of Finance decides the dispute."
    ),
)
CODE_SOURCE = Source(
    id="nyc-dof-violation-codes",
    title="Violation Codes, Fines, Rules & Regulations — NYC Department of Finance",
    url=CODES_URL,
    jurisdiction="New York City",
    topic="Violation code 38",
    accessed_at=ACCESS_DATE,
    relevant_excerpt=(
        "Code 38 is failing to show a parking meter receipt or tag in the windshield. "
        "The page also describes a five-minute grace period around the purchase and expiration times."
    ),
)


def _source_pair() -> list[Source]:
    return [CODE_SOURCE, REQUIRED_SOURCE]


def _question(id: str, prompt: str, kind: str, options=None) -> Question:
    return Question(id=id, prompt=prompt, type=kind, options=options or [])


def _same_plate(left: str, right: str) -> bool:
    normalize = lambda value: "".join(ch for ch in value.upper() if ch.isalnum())
    return normalize(left) == normalize(right)


def evaluate(confirmed_fields: TicketFields, answers: Answers, documents: list[Document]) -> Analysis:
    """Evaluate only the supported NYC DOF code 38 + ParkNYC evidence scenario."""
    missing: list[str] = []
    questions: list[Question] = []

    if answers.payment_method is None or answers.payment_method == "unknown":
        missing.append("How the parking session was paid for")
        questions.append(_question(
            "payment_method", "How did you pay for parking?", "choice",
            [
                {"value": "parknyc", "label": "ParkNYC"},
                {"value": "other", "label": "Another method"},
                {"value": "none", "label": "I did not pay"},
                {"value": "unknown", "label": "I am not sure"},
            ],
        ))
    elif answers.payment_method != "parknyc":
        return Analysis(
            status="no_supported_ground_identified",
            summary="This demo review only checks code 38 cases with a ParkNYC parking session. The information provided does not establish that scenario.",
            next_steps=["Review the official dispute guidance and provide evidence that directly relates to the allegation on the ticket."],
            sources=_source_pair(),
        )

    if answers.evidence_document_id is None or not any(
        d.kind == "evidence" and d.document_id == answers.evidence_document_id for d in documents
    ):
        missing.append("A ParkNYC receipt or payment record uploaded as evidence")
        questions.append(_question("evidence_document_id", "Upload and select the ParkNYC receipt or payment record.", "evidence"))
    if answers.session_start is None:
        missing.append("ParkNYC session start time")
        questions.append(_question("session_start", "What is the session start date and time shown in ParkNYC?", "datetime"))
    if answers.session_end is None:
        missing.append("ParkNYC session end time")
        questions.append(_question("session_end", "What is the session end date and time shown in ParkNYC?", "datetime"))
    if answers.session_plate_number is None:
        missing.append("Vehicle plate number shown in ParkNYC")
        questions.append(_question("session_plate_number", "What plate number is shown in the ParkNYC record?", "text"))
    if answers.session_plate_state is None:
        missing.append("Vehicle plate state shown in ParkNYC")
        questions.append(_question("session_plate_state", "What state is shown with the plate in ParkNYC?", "text"))
    if answers.session_zone is None:
        missing.append("ParkNYC zone number")
        questions.append(_question("session_zone", "What six-digit zone number is shown in ParkNYC?", "text"))
    if answers.zone_matches_ticket_location is None:
        missing.append("Whether the ParkNYC zone matches the ticket location")
        questions.append(_question("zone_matches_ticket_location", "Did you independently check that the ParkNYC zone matches the ticket location?", "boolean"))
    if answers.receipt_details_confirmed is None:
        missing.append("Confirmation that the uploaded payment record is accurate")
        questions.append(_question("receipt_details_confirmed", "Have you checked the uploaded record and confirmed its details are accurate?", "boolean"))

    if missing:
        return Analysis(
            status="needs_information",
            summary="More user-confirmed parking-session information is needed. TicketClear does not infer missing facts from an uploaded file.",
            missing_information=missing,
            questions=questions,
            next_steps=["Check each answer against the original ParkNYC record before continuing."],
            sources=_source_pair(),
        )

    # From here the values are present, but must still be internally consistent.
    assert answers.session_start and answers.session_end
    assert answers.session_plate_number and answers.session_plate_state
    assert answers.evidence_document_id
    start = datetime.fromisoformat(answers.session_start)
    end = datetime.fromisoformat(answers.session_end)
    ticket_time = datetime.fromisoformat(f"{confirmed_fields.issue_date}T{confirmed_fields.issue_time}")
    if end <= start:
        return Analysis(
            status="needs_information", summary="The ParkNYC session end must be later than its start.",
            missing_information=["A valid ParkNYC session time interval"],
            questions=[_question("session_end", "Please correct the ParkNYC session end date and time.", "datetime")],
            sources=_source_pair(),
        )

    mismatches = []
    if not _same_plate(confirmed_fields.plate_number or "", answers.session_plate_number):
        mismatches.append("The vehicle plate in the ticket and ParkNYC record does not match.")
    if (confirmed_fields.plate_state or "").upper() != answers.session_plate_state.upper():
        mismatches.append("The plate state in the ticket and ParkNYC record does not match.")
    if not answers.zone_matches_ticket_location:
        mismatches.append("The user has not confirmed that the ParkNYC zone matches the ticket location.")
    if not answers.receipt_details_confirmed:
        mismatches.append("The user has not confirmed the uploaded payment record's details.")
    # NYC DOF publishes a five-minute grace period around the purchase and expiry times.
    if not (start - timedelta(minutes=5) <= ticket_time <= end + timedelta(minutes=5)):
        mismatches.append("The ticket time is outside the ParkNYC session and the published five-minute grace period.")

    if mismatches:
        finding = Finding(
            id="parknyc-session-mismatch", title="The payment record does not yet match all ticket details",
            explanation=" ".join(mismatches),
            supporting_fact_ids=["confirmed_fields.plate_number", "confirmed_fields.plate_state", "answers.session_start", "answers.session_end", "answers.session_zone"],
            source_ids=[CODE_SOURCE.id],
            limitations=["This is a consistency check based on information entered by the user; TicketClear cannot independently verify the ParkNYC account or the physical signs."],
            suggested_next_step="Recheck the original ticket and ParkNYC record. Correct any transcription errors; do not change facts that are accurate.",
        )
        return Analysis(
            status="no_supported_ground_identified", summary="The supplied payment details do not currently establish a matching ParkNYC session for this ticket.",
            findings=[finding], next_steps=[finding.suggested_next_step], sources=_source_pair(),
        )

    finding = Finding(
        id="matching-parknyc-session", title="The supplied ParkNYC record appears consistent with the ticket",
        explanation=(
            "The user-confirmed ParkNYC record identifies the same normalized plate and state, "
            "the user confirms the zone matches the ticket location, and the ticket time falls "
            "within the session interval including the published five-minute grace period. "
            "This may support an explanation that parking was paid for, but it does not prove "
            "that the required receipt or tag was displayed or guarantee dismissal."
        ),
        supporting_fact_ids=["confirmed_fields.violation_code", "confirmed_fields.issue_date", "confirmed_fields.issue_time", "answers.payment_method", "answers.evidence_document_id", "answers.session_start", "answers.session_end", "answers.session_plate_number", "answers.session_plate_state", "answers.session_zone"],
        source_ids=[CODE_SOURCE.id, REQUIRED_SOURCE.id],
        limitations=[
            "TicketClear does not access ParkNYC directly; receipt details and zone match are user-confirmed.",
            "Proof of payment is not a guarantee that a judge will dismiss a failure-to-display violation.",
            "The user must verify all facts and submit the hearing request themselves.",
        ],
        suggested_next_step="Review the ticket and original ParkNYC record, then decide whether this statement accurately describes what happened.",
    )
    return Analysis(
        status="ready_for_draft", summary="The supplied facts are consistent with a ParkNYC payment during the ticketed time. A draft can be prepared for the user to review.",
        findings=[finding], next_steps=[finding.suggested_next_step, "NYC DOF says a hearing request should be made within 30 days of the ticket date to avoid late penalties."],
        sources=_source_pair(), draft_available=True,
    )
