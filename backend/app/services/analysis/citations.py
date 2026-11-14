"""Official routing and factual statements for civil citations."""
import json
from functools import lru_cache
from pathlib import Path

from app.models import Analysis, Case, Finding, Source

REGISTRY = Path(__file__).resolve().parents[4] / "knowledge" / "citation-sources.json"


@lru_cache
def sources() -> dict[str, Source]:
    records = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {record["id"]: Source.model_validate(record) for record in records}


def analyze_citation(case: Case, *, is_nyc: bool, is_dof: bool) -> Analysis:
    ticket = case.confirmed_fields
    source_id = "us-state-agencies"
    if ticket.jurisdiction_state == "NY" and is_nyc:
        if is_dof and ticket.ticket_type in {"parking", "camera"}:
            source_id = "nyc-dof-filing"
        elif ticket.ticket_type == "moving" and (ticket.issuing_authority or "").casefold() in {
            "new york state dmv", "ny dmv", "nypd", "new york city police department",
            "traffic violations bureau", "new york state department of motor vehicles",
        }:
            source_id = "nyc-dmv-tvb"
    source = sources()[source_id]
    step = {
        "nyc-dof-filing": "Check the NYC Department of Finance hearing instructions against your notice.",
        "nyc-dmv-tvb": "Check whether your notice is marked for TVB. Follow the instructions on the notice if it names a local court.",
        "us-state-agencies": "Use the agency or court named on your notice to confirm where and how to respond. The state government directory can help you find its official website.",
    }[source_id]
    required = {
        "jurisdiction_state": "State where the ticket was issued",
        "issuing_authority": "Agency or court named on the ticket",
        "ticket_number": "Ticket or notice number",
    }
    missing = [label for name, label in required.items() if not getattr(ticket, name)]
    if ticket.ticket_type in (None, "unknown"):
        missing.append("Confirm a supported civil ticket type")
    if not case.circumstances:
        missing.append("Describe what happened and what you want the authority to review")
    if missing:
        return Analysis(
            status="needs_information", summary="Add the remaining details to prepare a factual statement.",
            missing_information=missing, next_steps=[step], sources=[source],
        )
    return Analysis(
        status="ready_for_draft", draft_available=True, draft_kind="factual",
        summary="You can prepare a factual statement using your confirmed ticket details and your account of what happened.",
        findings=[Finding(
            id="factual-statement", title="Ticket details and your statement",
            explanation="Your draft will identify the notice and include the circumstances you entered.",
            supporting_fact_ids=["confirmed_fields.ticket_number", "confirmed_fields.issuing_authority"],
            source_ids=[source.id],
            limitations=["No legal defense, filing deadline, or eligibility has been verified for this case."],
            suggested_next_step=step,
        )],
        next_steps=[step], sources=[source],
    )
