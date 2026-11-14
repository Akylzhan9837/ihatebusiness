from datetime import date
from io import BytesIO
import sqlite3

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from app.api.errors import ApiError
from app.config import Settings
from app.main import create_app
from app.models import Analysis, ExtractedField, Extraction, Source, TicketFields


class TestExtractor:
    __test__ = False
    error = False

    async def extract(self, document, content):
        if self.error:
            raise ApiError(503, "ai_unavailable", "Try again.", retryable=True)
        assert content.startswith(b"\x89PNG")
        return Extraction(fields={
            name: ExtractedField(
                value="21" if name == "violation_code" else None,
                page=1 if name == "violation_code" else None,
                source_document_id=document.document_id,
                source_text="Violation code 21" if name == "violation_code" else None,
            ) for name in TicketFields.model_fields
        }, warnings=[])


def evaluate_test_rule(fields, answers, documents):
    if not answers.receipt_details_confirmed:
        return Analysis(status="needs_information", summary="Missing receipt details.")
    return Analysis(status="ready_for_draft", summary="Test rule.", sources=[
        Source(
            id="nyc-dof-dispute", title="Dispute a Ticket", jurisdiction="NYC", topic="Filing",
            accessed_at=date(2026, 11, 14), relevant_excerpt="Hearing options",
            url="https://www.nyc.gov/site/finance/vehicles/dispute-a-ticket.page",
        ),
    ])


FIELDS = {
    "ticket_number": "0000000012", "city": "NYC", "issuing_authority": "NYC Department of Finance",
    "violation_code": "38", "issue_date": "2026-11-02", "issue_time": "13:30",
    "location": "100 Example Ave", "plate_number": "DEMO123", "plate_state": "NY",
}


@pytest.fixture
def api(tmp_path):
    settings = Settings(db=tmp_path / "cases.sqlite3", demo_access=True)
    extractor = TestExtractor()
    with TestClient(create_app(
        settings, extractor=extractor, evaluate=evaluate_test_rule, render_pdf=lambda d: b"%PDF-test",
    )) as client:
        yield client, settings, extractor


def open_case(client):
    response = client.post("/api/cases", json={"synthetic_only": True})
    assert response.status_code == 201
    access = response.json()
    return f"/api/cases/{access['case_id']}", {"Authorization": "Bearer " + access["access_secret"]}


def upload(client, path, headers, kind="ticket", mime="image/png"):
    image = BytesIO()
    Image.new("RGB", (16, 16)).save(image, "PNG")
    return client.post(
        path + "/documents", headers=headers, data={"kind": kind},
        files={"file": ("../../secret.png", image.getvalue(), mime)},
    )


def test_full_case_reopen_edit_export_and_delete(api):
    client, settings, _ = api
    path, headers = open_case(client)
    other_path, other_headers = open_case(client)
    assert client.get(path).status_code == 404
    assert client.get(path, headers=other_headers).status_code == 404

    uploaded = upload(client, path, headers)
    assert uploaded.status_code == 201
    assert uploaded.json()["filename"].startswith("ticket-")
    assert "secret" not in uploaded.json()["filename"]
    extracted = client.post(path + "/extract", headers=headers).json()
    assert extracted["fields"]["violation_code"]["needs_confirmation"]
    assert client.get(path, headers=headers).json()["confirmed_fields"]["violation_code"] is None

    fields = FIELDS | {"violation_code": "21"}
    assert client.patch(path, headers=headers, json={"confirmed_fields": fields}).status_code == 200
    assert client.post(path + "/analyze", headers=headers).json()["status"] == "unsupported"
    assert client.patch(path, headers=headers, json={"confirmed_fields": {"violation_code": "38"}}).status_code == 200
    assert client.post(path + "/analyze", headers=headers).json()["status"] == "needs_information"

    receipt = upload(client, path, headers, kind="evidence").json()
    answers = {
        "payment_method": "parknyc", "evidence_document_id": receipt["document_id"],
        "session_start": "2026-11-02T13:20", "session_end": "2026-11-02T14:20",
        "session_plate_number": "DEMO123", "session_plate_state": "NY", "session_zone": "123456",
        "zone_matches_ticket_location": True, "receipt_details_confirmed": True,
    }
    assert client.patch(path, headers=headers, json={"answers": answers}).status_code == 200
    assert client.post(path + "/analyze", headers=headers).json()["draft_available"]
    draft = client.post(path + "/draft", headers=headers, json={"demo_access": True}).json()
    assert "0000000012" in draft["text"]
    assert draft["attachments"][0]["document_id"] == receipt["document_id"]
    assert client.patch(path + "/draft", headers=headers, json={"text": "My edited statement"}).status_code == 200
    reopened = client.get(path, headers=headers)
    assert reopened.headers["cache-control"] == "no-store"
    assert reopened.json()["draft"]["text"] == "My edited statement"
    assert "access_secret" not in reopened.json()
    assert client.get(path + "/export", headers=headers).headers["content-type"] == "application/pdf"
    assert client.patch(path, headers=headers, json={"outcome": "submitted"}).json()["draft"]["stale"] is False
    assert client.patch(path, headers=headers, json={"confirmed_fields": {"issue_date": None}}).json()["draft"]["stale"]
    assert client.get(path + "/export", headers=headers).status_code == 409
    missing_date = client.post(path + "/analyze", headers=headers).json()
    assert missing_date["status"] == "needs_information"
    assert missing_date["missing_information"] == ["Issue date"]

    assert client.delete(path, headers=headers).status_code == 204
    assert client.get(path, headers=headers).status_code == 404
    assert client.get(other_path, headers=other_headers).status_code == 200
    with sqlite3.connect(settings.db) as db:
        assert db.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 1


def test_failed_extraction_leaves_manual_path(api):
    client, _, extractor = api
    path, headers = open_case(client)
    assert upload(client, path, headers, mime="image/jpeg").status_code == 415
    assert upload(client, path, headers).status_code == 201
    assert upload(client, path, headers).status_code == 409
    extractor.error = True
    failure = client.post(path + "/extract", headers=headers)
    assert failure.status_code == 503
    assert failure.json()["error"]["retryable"]
    assert client.get(path, headers=headers).json()["extraction"] is None
    assert client.patch(path, headers=headers, json={"confirmed_fields": FIELDS}).status_code == 200
    assert client.post(path + "/analyze", headers=headers).json()["status"] == "needs_information"


def test_invalid_input_does_not_reflect_content(api):
    client, _, _ = api
    path, headers = open_case(client)
    response = client.patch(path, headers=headers, json={"confirmed_fields": {"issue_date": "sensitive"}})
    assert response.status_code == 422
    assert "sensitive" not in response.text
    oversized = client.patch(path, headers=headers, content=b"a" * 66000)
    assert oversized.status_code == 413
