from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app
from app.models import ExtractedField, Extraction, TicketFields


class FakeExtractor:
    async def extract(self, document, content):
        values = {
            "ticket_number": "0000000012",
            "issuing_authority": "NYC Department of Finance",
            "city": "NYC",
            "violation_code": "38",
            "violation_description": "Failure to display parking meter receipt",
            "issue_date": "2026-11-02",
            "issue_time": "13:30",
            "location": "100 Example Ave",
            "amount": "65.00",
            "plate_number": "DEMO123",
            "plate_state": "NY",
        }
        return Extraction(fields={
            name: ExtractedField(
                value=values.get(name),
                source_document_id=document.document_id,
                page=1,
                source_text=f"Synthetic value: {values.get(name)}" if values.get(name) else None,
            ) for name in TicketFields.model_fields
        }, warnings=["Synthetic fixture extractor; not a real Gemini response."])


def png_bytes():
    image = BytesIO()
    Image.new("RGB", (16, 16), "white").save(image, "PNG")
    return image.getvalue()


def test_real_rules_and_pdf_full_api_path(tmp_path):
    settings = Settings(
        db=tmp_path / "e2e.sqlite3",
        demo_access=True,
        ai_key="test-key-not-used",
        ai_model="test-model",
        origins=(),
    )
    with TestClient(create_app(settings, extractor=FakeExtractor())) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/ready").status_code == 200

        created = client.post("/api/cases", json={"synthetic_only": True})
        assert created.status_code == 201
        access = created.json()
        path = f"/api/cases/{access['case_id']}"
        headers = {"Authorization": f"Bearer {access['access_secret']}"}

        ticket = client.post(
            path + "/documents",
            headers=headers,
            data={"kind": "ticket"},
            files={"file": ("synthetic-ticket.png", png_bytes(), "image/png")},
        )
        assert ticket.status_code == 201

        extracted = client.post(path + "/extract", headers=headers)
        assert extracted.status_code == 200
        assert extracted.json()["fields"]["violation_code"]["value"] == "38"

        confirmed = {
            "ticket_number": "0000000012",
            "issuing_authority": "NYC Department of Finance",
            "city": "NYC",
            "violation_code": "38",
            "violation_description": "Failure to display parking meter receipt",
            "issue_date": "2026-11-02",
            "issue_time": "13:30",
            "location": "100 Example Ave",
            "amount": "65.00",
            "plate_number": "DEMO123",
            "plate_state": "NY",
        }
        patch = client.patch(path, headers=headers, json={"confirmed_fields": confirmed})
        assert patch.status_code == 200

        evidence = client.post(
            path + "/documents",
            headers=headers,
            data={"kind": "evidence"},
            files={"file": ("synthetic-parknyc.png", png_bytes(), "image/png")},
        )
        assert evidence.status_code == 201

        answers = {
            "payment_method": "parknyc",
            "evidence_document_id": evidence.json()["document_id"],
            "session_start": "2026-11-02T13:20",
            "session_end": "2026-11-02T14:20",
            "session_plate_number": "DEMO123",
            "session_plate_state": "NY",
            "session_zone": "123456",
            "zone_matches_ticket_location": True,
            "receipt_details_confirmed": True,
        }
        assert client.patch(path, headers=headers, json={"answers": answers}).status_code == 200

        analysis = client.post(path + "/analyze", headers=headers)
        assert analysis.status_code == 200
        assert analysis.json()["status"] == "ready_for_draft"
        assert analysis.json()["draft_available"] is True

        draft = client.post(path + "/draft", headers=headers, json={"demo_access": True})
        assert draft.status_code == 200
        assert "0000000012" in draft.json()["text"]
        assert draft.json()["attachments"][0]["document_id"] == evidence.json()["document_id"]

        exported = client.get(path + "/export", headers=headers)
        assert exported.status_code == 200
        assert exported.headers["content-type"] == "application/pdf"
        assert exported.content.startswith(b"%PDF-")
