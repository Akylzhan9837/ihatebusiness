from app.api.errors import ApiError
from app.models import Attachment, Case, Draft, SubmissionStep
from app.services.analysis import matching_receipt
from app.storage import now


def draft_for(case: Case) -> Draft:
    attachment = matching_receipt(case)
    if attachment is None or case.analysis is None:
        raise ApiError(409, "draft_not_ready", "Run the case review before preparing a draft.")
    submission_url = next(
        (source.url for source in case.analysis.sources if source.id == "nyc-dof-dispute"), None,
    )
    if submission_url is None:
        raise ApiError(503, "rules_unavailable", "The official filing instructions could not be loaded.", retryable=True)

    fields = case.confirmed_fields
    answers = case.answers
    text = (
        "To the NYC Department of Finance:\n\n"
        f"I request a hearing to contest parking violation {fields.ticket_number} (code {fields.violation_code}). "
        f"The ticket records {fields.issue_date} at {fields.issue_time} at {fields.location}, "
        f"for plate {fields.plate_number} ({fields.plate_state}).\n\n"
        f"I paid for parking through ParkNYC in zone {answers.session_zone}. "
        f"The attached receipt lists plate {answers.session_plate_number} ({answers.session_plate_state}) "
        f"and a session from {answers.session_start.replace('T', ' ')} to {answers.session_end.replace('T', ' ')} "
        "local time. I checked that the parking zone matches the ticket location. "
        "Please review the attached receipt and dismiss the violation if warranted."
    )
    if case.circumstances:
        text += f"\n\nMy additional statement:\n{case.circumstances}"
    return Draft(
        text=text,
        attachments=[Attachment(document_id=attachment.document_id, filename=attachment.filename)],
        submission_steps=[
            SubmissionStep(text="Open the NYC Department of Finance dispute page and select a hearing method.", url=submission_url),
            SubmissionStep(text="Review the draft, provide the required ticket details, and submit the draft and a copy of the ParkNYC receipt yourself.", url=submission_url),
        ],
        updated_at=now(),
    )
