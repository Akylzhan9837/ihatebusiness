from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from anyio import Semaphore, WouldBlock
from fastapi import APIRouter, Depends, Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from app.api.errors import ApiError
from app.config import Settings
from app.models import (
    Analysis, Answers, Case, CaseAccess, CreateCase, DemoAccess, Document, Draft, Extraction,
    PatchCase, PatchDraft, TicketFields,
)
from app.services.analysis import RuleEvaluator, analyze
from app.services.drafting import draft_for
from app.services.extraction import Extractor
from app.services.extraction.files import MAX_FILE_BYTES, check_file
from app.storage import Store, now, unavailable_case


def make_router(
    store: Store,
    settings: Settings,
    extractor: Extractor,
    ai_slots: Semaphore,
    evaluate: RuleEvaluator | None,
    render_pdf: Callable[[Draft], bytes] | None,
) -> APIRouter:
    router = APIRouter(prefix="/api")

    def open_case(case_id: UUID, request: Request) -> tuple[Case, int]:
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or len(token) != 43 or not token.isascii():
            raise unavailable_case()
        return store.open(case_id, token)

    Access = Annotated[tuple[Case, int], Depends(open_case)]

    def invalidate(case: Case):
        case.analysis = None
        if case.draft is not None:
            case.draft.stale = True

    def current_draft(case: Case) -> Draft:
        if case.draft is None or case.draft.stale or case.analysis is None or not case.analysis.draft_available:
            raise ApiError(409, "draft_not_ready", "Prepare a current draft before continuing.")
        return case.draft

    @router.get("/health")
    def health():
        return {"status": "ok"}

    @router.get("/ready")
    def ready():
        missing = []
        if not (settings.ai_key and settings.ai_model):
            missing.append("ai_configuration")
        if evaluate is None:
            missing.append("rules")
        if render_pdf is None:
            missing.append("export")
        if missing:
            raise ApiError(503, "backend_not_ready", "Backend setup required: " + ", ".join(missing), retryable=True)
        return {"status": "ready"}

    @router.post("/cases", response_model=CaseAccess, status_code=201)
    def create_case(body: CreateCase):
        return store.create(body.jurisdiction_state)

    @router.get("/cases/{case_id}", response_model=Case)
    def get_case(access: Access):
        return access[0]

    @router.post(
        "/cases/{case_id}/documents", response_model=Document, status_code=201,
        openapi_extra={"requestBody": {"required": True, "content": {"multipart/form-data": {
            "schema": {"type": "object", "required": ["kind", "file"], "properties": {
                "kind": {"type": "string", "enum": ["ticket", "evidence"]},
                "file": {"type": "string", "format": "binary"},
            }}
        }}}},
    )
    async def upload_document(request: Request, access: Access):
        case, revision = access
        async with request.form(max_files=1, max_fields=1, max_part_size=1024) as form:
            kind = form.get("kind")
            file = form.get("file")
            if kind not in ("ticket", "evidence") or not isinstance(file, UploadFile):
                raise ApiError(422, "invalid_upload", "Provide a file and select ticket or evidence.")
            limit = 1 if kind == "ticket" else 4
            if sum(doc.kind == kind for doc in case.documents) >= limit:
                raise ApiError(409, "document_limit", "This case already has the maximum number of files of that type.")
            content = await file.read(MAX_FILE_BYTES + 1)
            document = await run_in_threadpool(check_file, kind, file.content_type, content)
        case.documents.append(document)
        invalidate(case)
        await run_in_threadpool(store.save, case, revision, (document, content))
        return document

    @router.post("/cases/{case_id}/extract", response_model=Extraction)
    async def extract_ticket(access: Access):
        case, revision = access
        if case.extraction is not None:
            return case.extraction
        ticket = next((doc for doc in case.documents if doc.kind == "ticket"), None)
        if ticket is None:
            raise ApiError(409, "ticket_required", "Upload a ticket before reading it.")
        try:
            ai_slots.acquire_nowait()
        except WouldBlock:
            raise ApiError(429, "ai_busy", "Ticket reading is busy. Try again shortly.", retryable=True) from None
        try:
            contents = await run_in_threadpool(store.file, case.case_id, ticket.document_id)
            case.extraction = await extractor.extract(ticket, contents)
            await run_in_threadpool(store.save, case, revision)
        finally:
            ai_slots.release()
        return case.extraction

    @router.patch("/cases/{case_id}", response_model=Case)
    def patch_case(body: PatchCase, access: Access):
        case, revision = access
        fields, circumstances, answers = case.confirmed_fields, case.circumstances, case.answers
        if body.confirmed_fields is not None:
            case.confirmed_fields = TicketFields.model_validate(
                fields.model_dump() | body.confirmed_fields.model_dump(exclude_unset=True),
            )
        if body.answers is not None:
            case.answers = Answers.model_validate(answers.model_dump() | body.answers.model_dump(exclude_unset=True))
        if "circumstances" in body.model_fields_set:
            case.circumstances = body.circumstances
        if "outcome" in body.model_fields_set:
            case.outcome = body.outcome
        if (fields, circumstances, answers) != (case.confirmed_fields, case.circumstances, case.answers):
            invalidate(case)
        store.save(case, revision)
        return case

    @router.post("/cases/{case_id}/analyze", response_model=Analysis)
    def analyze_case(access: Access):
        case, revision = access
        result = analyze(case, evaluate)
        if result != case.analysis:
            if case.draft is not None:
                case.draft.stale = True
            case.analysis = result
            store.save(case, revision)
        return result

    @router.post("/cases/{case_id}/draft", response_model=Draft)
    def create_draft(body: DemoAccess, access: Access):
        case, revision = access
        if not settings.demo_access:
            raise ApiError(409, "demo_unavailable", "Demo access is currently unavailable.")
        if case.analysis is None or not case.analysis.draft_available:
            raise ApiError(409, "draft_not_ready", "Complete the case review before preparing a draft.")
        if case.draft is not None and not case.draft.stale:
            return case.draft
        case.draft = draft_for(case)
        store.save(case, revision)
        return case.draft

    @router.patch("/cases/{case_id}/draft", response_model=Draft)
    def edit_draft(body: PatchDraft, access: Access):
        case, revision = access
        draft = current_draft(case)
        draft.text = body.text
        draft.updated_at = now()
        store.save(case, revision)
        return draft

    @router.get("/cases/{case_id}/export")
    def export_case(access: Access):
        draft = current_draft(access[0])
        if render_pdf is None:
            raise ApiError(503, "export_unavailable", "PDF export is temporarily unavailable. You can still copy your draft.", retryable=True)
        return Response(
            render_pdf(draft),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ticketclear-draft.pdf"},
        )

    @router.delete("/cases/{case_id}", status_code=204)
    def delete_case(access: Access):
        store.delete(access[0].case_id)
        return Response(status_code=204)

    return router
