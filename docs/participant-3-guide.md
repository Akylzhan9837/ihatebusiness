# Participant 3 — Rules, QA, knowledge and PDF export

## Your responsibility

The API contract assigns participant 3 the following areas:

- `backend/app/rules/` — evidence-led scenario evaluation.
- `backend/app/export/` — PDF export of a reviewed draft.
- `knowledge/` — official source registry.
- `fixtures/` — synthetic positive and negative examples.
- `backend/tests/e2e/` — full API path test.
- `docs/` — integration notes and QA instructions.

The agreed MVP scenario in `docs/api-contract.md` is **NYC Department of Finance, violation code 38, with ParkNYC payment evidence**. Do not switch to broken meter without a team decision and changes to the API's `Answers` model, frontend questions, analysis checks, drafting, fixtures and tests.

## Interfaces

```python
# backend/app/rules/__init__.py
from app.models import Analysis, Answers, Document, TicketFields

def evaluate(
    confirmed_fields: TicketFields,
    answers: Answers,
    documents: list[Document],
) -> Analysis:
    ...
```

```python
# backend/app/export/__init__.py
from app.models import Draft

def render_pdf(draft: Draft) -> bytes:
    ...
```

These are the exact interfaces loaded by `app.main.create_app()`.

## Rule behavior

- Return `needs_information` when required user-confirmed answers or evidence are missing.
- Return `no_supported_ground_identified` for conflicting details or a payment method outside this MVP scenario.
- Return `ready_for_draft` only when the selected evidence document belongs to this case, the user confirms its details, plate and state match, the user confirms the zone/location match, and ticket time falls in the payment interval including the specified five-minute allowance.
- Never claim TicketClear independently accessed ParkNYC or independently verified the zone.
- Never guarantee ticket dismissal. State limitations in findings.
- Include the official `nyc-dof-dispute` source when draft preparation is allowed.

## PDF behavior

`render_pdf(draft)` returns PDF bytes. The PDF includes the draft text, attachment checklist and official submission steps. It does not fetch, embed or submit evidence files. It must clearly say the draft requires user review and has not been submitted.

## Run tests (Windows PowerShell)

From the `backend` directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Install `requirements-p3.txt` as well: the PDF renderer uses ReportLab. The e2e test uses a deterministic fake extractor so it does not spend Gemini API quota. It uses the real rules and real PDF renderer. A separate manual smoke test with Gemini requires `GEMINI_API_KEY` and `GEMINI_MODEL`.

## GitHub workflow

Create a branch from the latest `main` (or the team-agreed integration base):

```bash
git switch main
git pull origin main
git switch -c feature/rules-qa
```

Copy only participant-3-owned files into that checkout. Review `git status` and `git diff`. Then:

```bash
git add backend/app/rules backend/app/export backend/tests/e2e knowledge fixtures docs
 git add backend/tests/test_rules_export.py
 git commit -m "Add ParkNYC rules, PDF export and QA fixtures"
git push -u origin feature/rules-qa
```

Open a Pull Request from `feature/rules-qa` into the agreed base branch. Do not push directly to `main`. If the repository's current branch names differ, coordinate the base with participant 1 before merging.

## Before merge

- [ ] Confirm `feature/rules-qa` exists on GitHub.
- [ ] Confirm the PR includes only intended files.
- [ ] All backend tests pass.
- [ ] `/api/ready` returns 200 with Gemini env vars configured and rules/export present.
- [ ] Frontend can create a case, upload a synthetic ticket, confirm fields, add ParkNYC evidence, analyze, create draft and download PDF with mocks disabled.
- [ ] No `.env`, API key, real ticket or personal data is committed.
