# Rules and export JSON examples

Python functions accept Pydantic models, not raw dictionaries. The following JSON illustrates their serialized shape.

## evaluate input (simplified)

```json
{
  "confirmed_fields": {
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
    "plate_state": "NY"
  },
  "answers": {
    "payment_method": "parknyc",
    "evidence_document_id": "11111111-1111-4111-8111-111111111111",
    "session_start": "2026-11-02T13:20",
    "session_end": "2026-11-02T14:20",
    "session_plate_number": "DEMO123",
    "session_plate_state": "NY",
    "session_zone": "123456",
    "zone_matches_ticket_location": true,
    "receipt_details_confirmed": true
  },
  "documents": [
    {
      "document_id": "11111111-1111-4111-8111-111111111111",
      "kind": "evidence",
      "filename": "evidence-example.png",
      "media_type": "image/png",
      "size_bytes": 1200
    }
  ]
}
```

## evaluate result (shape example)

```json
{
  "status": "ready_for_draft",
  "summary": "The supplied facts are consistent with a ParkNYC payment during the ticketed time. A draft can be prepared for the user to review.",
  "findings": [
    {
      "id": "matching-parknyc-session",
      "title": "The supplied ParkNYC record appears consistent with the ticket",
      "explanation": "The user-confirmed plate, state, zone and time details appear consistent.",
      "supporting_fact_ids": ["confirmed_fields.plate_number", "answers.session_start", "answers.session_end"],
      "source_ids": ["nyc-dof-violation-codes", "nyc-dof-dispute"],
      "limitations": ["TicketClear does not access ParkNYC directly.", "This does not guarantee dismissal."],
      "suggested_next_step": "Review the original ticket and ParkNYC record before deciding whether to submit."
    }
  ],
  "missing_information": [],
  "questions": [],
  "next_steps": ["Review all facts and official instructions."],
  "sources": [
    {
      "id": "nyc-dof-dispute",
      "title": "Dispute a Ticket — NYC Department of Finance",
      "url": "https://www.nyc.gov/site/finance/vehicles/dispute-a-ticket.page",
      "jurisdiction": "New York City",
      "topic": "Hearing process and filing deadline",
      "accessed_at": "2026-11-15",
      "relevant_excerpt": "Use the official page to review current hearing instructions."
    }
  ],
  "draft_available": true
}
```

The actual implementation can return additional findings and sources. All IDs in `finding.source_ids` must exist in `Analysis.sources`.

## render_pdf input

```json
{
  "text": "To the NYC Department of Finance...",
  "attachments": [
    {
      "document_id": "11111111-1111-4111-8111-111111111111",
      "filename": "evidence-example.png"
    }
  ],
  "submission_steps": [
    {
      "text": "Open the NYC Department of Finance dispute page and review the hearing instructions.",
      "url": "https://www.nyc.gov/site/finance/vehicles/dispute-a-ticket.page"
    }
  ],
  "stale": false,
  "updated_at": "2026-11-15T12:00:00"
}
```

Output: raw PDF bytes (`application/pdf`), not JSON. The evidence is listed in the PDF but is not embedded; the user attaches the original evidence separately.
