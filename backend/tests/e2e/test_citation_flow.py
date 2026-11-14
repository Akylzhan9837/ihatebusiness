from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.config import Settings
from app.main import create_app


def test_other_state_civil_citation_draft_can_be_reopened_and_exported(tmp_path):
    app = create_app(Settings(db=tmp_path / "cases.sqlite", demo_access=True))
    with TestClient(app) as client:
        created = client.post("/api/cases", json={"synthetic_only": True, "jurisdiction_state": "CA"})
        assert created.status_code == 201
        case = created.json()
        route = f"/api/cases/{case['case_id']}"
        auth = {"Authorization": f"Bearer {case['access_secret']}"}

        saved = client.patch(route, headers=auth, json={"confirmed_fields": {
            "ticket_type": "other_civil",
            "issuing_authority": "Example County",
            "ticket_number": "ABC-123",
            "violation_code": "CIV-4.A",
        }})
        assert saved.status_code == 200
        assert saved.json()["confirmed_fields"]["jurisdiction_state"] == "CA"
        result = client.post(route + "/analyze", headers=auth).json()
        assert result["status"] == "needs_information"
        assert result["sources"][0]["url"] == "https://www.usa.gov/state-governments"

        statement = "I am asking the agency to review the date on this notice."
        client.patch(route, headers=auth, json={"circumstances": statement})
        result = client.post(route + "/analyze", headers=auth).json()
        assert result["status"] == "ready_for_draft"
        assert result["draft_kind"] == "factual"

        draft = client.post(route + "/draft", headers=auth, json={"demo_access": True}).json()
        assert statement in draft["text"]
        assert "ABC-123" in draft["text"]
        assert "ParkNYC" not in draft["text"]
        assert client.get(route, headers=auth).json()["draft"]["text"] == draft["text"]
        pdf = client.get(route + "/export", headers=auth)
        assert pdf.status_code == 200
        assert "ABC-123" in PdfReader(BytesIO(pdf.content)).pages[0].extract_text()
