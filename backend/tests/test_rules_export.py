from datetime import date
from uuid import uuid4

from app.export import render_pdf
from app.models import Answers, Document, Draft, SubmissionStep, TicketFields
from app.rules import evaluate


def sample():
    evidence_id = uuid4()
    fields = TicketFields(
        ticket_number="0000000012", issuing_authority="NYC Department of Finance", city="NYC",
        violation_code="38", issue_date="2026-11-02", issue_time="13:30",
        location="100 Example Ave", plate_number="DEMO123", plate_state="NY",
    )
    answers = Answers(
        payment_method="parknyc", evidence_document_id=evidence_id,
        session_start="2026-11-02T13:20", session_end="2026-11-02T14:20",
        session_plate_number="DEMO-123", session_plate_state="NY", session_zone="123456",
        zone_matches_ticket_location=True, receipt_details_confirmed=True,
    )
    docs = [Document(document_id=evidence_id, kind="evidence", filename="evidence-demo.png", media_type="image/png", size_bytes=100)]
    return fields, answers, docs


def test_rule_ready_when_parknyc_details_match():
    fields, answers, docs = sample()
    result = evaluate(fields, answers, docs)
    assert result.status == "ready_for_draft"
    assert result.draft_available is True
    assert {source.id for source in result.sources} >= {"nyc-dof-dispute", "nyc-dof-violation-codes"}


def test_rule_requests_missing_evidence():
    fields, answers, docs = sample()
    answers.evidence_document_id = None
    result = evaluate(fields, answers, docs)
    assert result.status == "needs_information"
    assert "evidence_document_id" in {question.id for question in result.questions}


def test_rule_does_not_claim_mismatched_plate_is_supported():
    fields, answers, docs = sample()
    answers.session_plate_number = "OTHER99"
    result = evaluate(fields, answers, docs)
    assert result.status == "no_supported_ground_identified"
    assert result.draft_available is False


def test_pdf_export_returns_pdf_and_includes_review_warning():
    draft = Draft(
        text="To the NYC Department of Finance:\n\nI request a hearing.",
        attachments=[],
        submission_steps=[SubmissionStep(text="Open official dispute page.", url="https://www.nyc.gov/site/finance/vehicles/dispute-a-ticket.page")],
        updated_at="2026-11-15T12:00:00",
    )
    result = render_pdf(draft)
    assert result.startswith(b"%PDF-")
    assert len(result) > 500


def test_app_discovers_real_rules_and_pdf_plugins(tmp_path):
    from fastapi.testclient import TestClient
    from app.config import Settings
    from app.main import create_app

    app = create_app(Settings(db=tmp_path / "ready.sqlite3", ai_key="", ai_model=""))
    with TestClient(app) as client:
        response = client.get("/api/ready")
    assert response.status_code == 503
    assert response.json()["error"]["message"].endswith("ai_configuration")


def test_real_rules_to_draft_to_pdf_flow(tmp_path):
    from io import BytesIO
    from fastapi.testclient import TestClient
    from PIL import Image
    from app.config import Settings
    from app.main import create_app

    image = BytesIO()
    Image.new("RGB", (16, 16)).save(image, "PNG")
    with TestClient(create_app(Settings(db=tmp_path / "flow.sqlite3", demo_access=True))) as client:
        created = client.post("/api/cases", json={"synthetic_only": True}).json()
        path = f"/api/cases/{created['case_id']}"
        headers = {"Authorization": f"Bearer {created['access_secret']}"}
        uploaded = client.post(
            path + "/documents", headers=headers, data={"kind": "evidence"},
            files={"file": ("receipt.png", image.getvalue(), "image/png")},
        )
        assert uploaded.status_code == 201
        evidence_id = uploaded.json()["document_id"]
        patch = client.patch(path, headers=headers, json={
            "confirmed_fields": {
                "ticket_number": "0000000012", "issuing_authority": "NYC Department of Finance", "city": "NYC",
                "violation_code": "38", "issue_date": "2026-11-02", "issue_time": "13:30",
                "location": "100 Example Ave", "plate_number": "DEMO123", "plate_state": "NY",
            },
            "answers": {
                "payment_method": "parknyc", "evidence_document_id": evidence_id,
                "session_start": "2026-11-02T13:20", "session_end": "2026-11-02T14:20",
                "session_plate_number": "DEMO123", "session_plate_state": "NY", "session_zone": "123456",
                "zone_matches_ticket_location": True, "receipt_details_confirmed": True,
            },
        })
        assert patch.status_code == 200
        analysis = client.post(path + "/analyze", headers=headers)
        assert analysis.status_code == 200
        assert analysis.json()["status"] == "ready_for_draft"
        draft = client.post(path + "/draft", headers=headers, json={"demo_access": True})
        assert draft.status_code == 200
        exported = client.get(path + "/export", headers=headers)
        assert exported.status_code == 200
        assert exported.headers["content-type"] == "application/pdf"
        assert exported.content.startswith(b"%PDF-")


def test_five_minute_grace_is_included_but_six_minutes_is_not():
    fields, answers, docs = sample()
    answers.session_start = "2026-11-02T13:30"
    answers.session_end = "2026-11-02T14:30"
    fields.issue_time = "13:25"
    assert evaluate(fields, answers, docs).status == "ready_for_draft"
    fields.issue_time = "13:24"
    assert evaluate(fields, answers, docs).status == "no_supported_ground_identified"
