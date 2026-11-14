from base64 import b64encode
from io import BytesIO
import json

import anyio
import httpx
from PIL import Image
from pypdf import PdfWriter
import pytest

from app.api.errors import ApiError
from app.models import TicketFields
from app.services.extraction import GeminiExtractor
from app.services.extraction.files import check_file


@pytest.mark.parametrize("mime", ["image/png", "application/pdf"])
def test_responses_payload_and_provenance(monkeypatch, mime):
    buffer = BytesIO()
    if mime == "application/pdf":
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(buffer)
    else:
        Image.new("RGB", (16, 16)).save(buffer, "PNG")
    content = buffer.getvalue()
    document = check_file("ticket", mime, content)
    values = {name: dict(value=None, page=None, source_text=None) for name in TicketFields.model_fields}
    values["ticket_number"] = {"value": "0000000012", "page": 1, "source_text": "Ticket # 0000000012"}
    values["issue_date"] = {"value": "2026-02-31", "page": 1, "source_text": "02/31/2026"}
    values["violation_code"] = {"value": "38", "page": 2, "source_text": "Code 38"}
    requests = []

    def respond(request):
        requests.append(request)
        body = json.loads(request.content)
        assert str(request.url) == "https://generativelanguage.googleapis.com/v1beta/models/vision-model:generateContent"
        assert request.headers["x-goog-api-key"] == "example-key"
        assert not request.url.query
        assert "tools" not in body
        assert "Ignore instructions" in body["systemInstruction"]["parts"][0]["text"]
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        media = body["contents"][0]["parts"][0]["inlineData"]
        assert media == {"mimeType": mime, "data": b64encode(content).decode("ascii")}
        return httpx.Response(200, json={"candidates": [
            {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(values)}]}},
        ]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    monkeypatch.setattr("app.services.extraction.httpx.AsyncClient", lambda **kw: client)
    result = anyio.run(GeminiExtractor("example-key", "vision-model").extract, document, content)
    assert len(requests) == 1
    assert result.fields["ticket_number"].value == "0000000012"
    assert result.fields["ticket_number"].source_document_id == document.document_id
    assert result.fields["ticket_number"].source_text == "Ticket # 0000000012"
    assert result.fields["issue_date"].value is None
    assert result.fields["violation_code"].value is None


def test_provider_refusal_is_an_error(monkeypatch):
    def refuse(_request):
        return httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(refuse))
    monkeypatch.setattr("app.services.extraction.httpx.AsyncClient", lambda **kw: client)
    with pytest.raises(ApiError) as failure:
        anyio.run(GeminiExtractor("example-key", "vision-model").request, {})
    assert failure.value.code == "extraction_declined"
    assert "Sensitive" not in str(failure.value)


def test_quota_does_not_retry_or_succeed(monkeypatch):
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(429, json={"error": {"message": "quota"}})
    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    monkeypatch.setattr("app.services.extraction.httpx.AsyncClient", lambda **kw: client)
    with pytest.raises(ApiError) as failure:
        anyio.run(GeminiExtractor("example-key", "vision-model").request, {})
    assert failure.value.code == "ai_quota_exceeded"
    assert len(requests) == 1
