from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


ShortText = Annotated[str, StringConstraints(min_length=1, max_length=250)]
NoticeIdentifier = Annotated[str, StringConstraints(min_length=1, max_length=64)]
JurisdictionState = Literal[
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
    "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
    "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI",
    "WY",
]
TicketType = Literal["parking", "camera", "moving", "other_civil", "unknown"]
DateText = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$")]
TimeText = Annotated[str, StringConstraints(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")]
DateTimeText = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d$")]
PlateState = Annotated[str, StringConstraints(pattern=r"^[A-Za-z]{2}$")]
DocumentKind = Literal["ticket", "evidence"]


class TicketFields(Model):
    jurisdiction_state: JurisdictionState | None = None
    ticket_type: TicketType | None = None
    ticket_number: NoticeIdentifier | None = None
    issuing_authority: ShortText | None = None
    city: ShortText | None = None
    violation_code: NoticeIdentifier | None = None
    violation_description: ShortText | None = None
    issue_date: DateText | None = None
    issue_time: TimeText | None = None
    location: ShortText | None = None
    amount: Annotated[str, StringConstraints(pattern=r"^\d{1,6}(?:\.\d{1,2})?$")] | None = None
    plate_number: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9 -]{1,12}$")] | None = None
    plate_state: PlateState | None = None

    @field_validator("issue_date")
    @classmethod
    def valid_date(cls, value: str | None) -> str | None:
        if value is not None:
            date.fromisoformat(value)
        return value

    @field_validator("plate_number")
    @classmethod
    def valid_plate(cls, value: str | None) -> str | None:
        if value is not None and not any(character.isalnum() for character in value):
            raise ValueError("Enter a plate number.")
        return value


class Answers(Model):
    payment_method: Literal["parknyc", "other", "none", "unknown"] | None = None
    evidence_document_id: UUID | None = None
    session_start: DateTimeText | None = None
    session_end: DateTimeText | None = None
    session_plate_number: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9 -]{1,12}$")] | None = None
    session_plate_state: PlateState | None = None
    session_zone: Annotated[str, StringConstraints(pattern=r"^\d{6}$")] | None = None
    zone_matches_ticket_location: bool | None = None
    receipt_details_confirmed: bool | None = None

    @field_validator("session_start", "session_end")
    @classmethod
    def valid_local_datetime(cls, value: str | None) -> str | None:
        if value is not None:
            datetime.fromisoformat(value)
        return value


class Document(Model):
    document_id: UUID
    kind: DocumentKind
    filename: str
    media_type: Literal["application/pdf", "image/jpeg", "image/png"]
    size_bytes: int


class ExtractedField(Model):
    value: str | None
    source_document_id: UUID
    page: int | None
    source_text: str | None
    needs_confirmation: Literal[True] = True


class Extraction(Model):
    fields: dict[str, ExtractedField]
    warnings: list[str]


class Option(Model):
    value: str
    label: str


class Question(Model):
    id: str
    prompt: str
    type: Literal["choice", "text", "datetime", "boolean", "evidence"]
    options: list[Option] = []


class Source(Model):
    id: str
    title: str
    url: str
    jurisdiction: str
    topic: str
    accessed_at: date
    relevant_excerpt: str


class Finding(Model):
    id: str
    title: str
    explanation: str
    supporting_fact_ids: list[str]
    source_ids: list[str]
    limitations: list[str]
    suggested_next_step: str


AnalysisStatus = Literal["unsupported", "needs_information", "no_supported_ground_identified", "ready_for_draft"]


class Analysis(Model):
    status: AnalysisStatus
    summary: str
    findings: list[Finding] = []
    missing_information: list[str] = []
    questions: list[Question] = []
    next_steps: list[str] = []
    sources: list[Source] = []
    draft_available: bool = False
    draft_kind: Literal["factual"] | None = None


class Attachment(Model):
    document_id: UUID
    filename: str


class SubmissionStep(Model):
    text: str
    url: str


class Draft(Model):
    text: str
    attachments: list[Attachment]
    submission_steps: list[SubmissionStep]
    stale: bool = False
    updated_at: datetime


class Offer(Model):
    price_cents: Literal[1900] = 1900
    currency: Literal["USD"] = "USD"
    mode: Literal["demo", "unavailable"]
    charge: Literal[False] = False


Outcome = Literal["submitted", "dismissed", "upheld", "other"]


class Case(Model):
    case_id: UUID
    documents: list[Document] = []
    extraction: Extraction | None = None
    confirmed_fields: TicketFields = TicketFields()
    circumstances: str | None = None
    answers: Answers = Answers()
    outcome: Outcome | None = None
    analysis: Analysis | None = None
    draft: Draft | None = None
    offer: Offer
    created_at: datetime
    updated_at: datetime


class CreateCase(Model):
    jurisdiction_state: JurisdictionState | None = None
    synthetic_only: Literal[True]


class CaseAccess(Model):
    case_id: UUID
    access_secret: str


class PatchCase(Model):
    confirmed_fields: TicketFields | None = None
    circumstances: Annotated[str, StringConstraints(max_length=4000)] | None = None
    answers: Answers | None = None
    outcome: Outcome | None = None


class DemoAccess(Model):
    demo_access: Literal[True]


class PatchDraft(Model):
    text: Annotated[str, StringConstraints(min_length=1, max_length=16000)]
