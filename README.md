# Ticky

Ticky is a browser-based tool for reviewing U.S. parking tickets, camera citations, and other supported civil or traffic notices. It helps you check the details, organize evidence, and prepare an editable statement you can submit yourself.

**[Try the live demo](https://akylzhan9837.github.io/ihatebusiness/)** · Free to try · No account required · Synthetic documents only

[GitHub Pages frontend](https://akylzhan9837.github.io/ihatebusiness/) uses the live FastAPI API configured in the repository's `TICKY_API_BASE_URL` Actions variable. When changing the API host, update that variable and rerun the Pages workflow. Set `TICKETCLEAR_CORS_ORIGINS=https://akylzhan9837.github.io` on the backend for the Pages origin.

Built by **ihatebusiness** for **Business Cup 2.0**.

## How it works

1. Choose the state that issued the notice. Upload a PDF, JPG, or PNG, or enter the details manually.
2. Review the fields Gemini extracted and confirm or correct them.
3. Add your account of what happened and any relevant evidence. The app flags missing information and points to official resources.
4. Generate an editable statement when the review is ready. Save your changes, download a PDF, or return to your case using its private link.

### ParkNYC demo case

The most detailed workflow covers NYC parking violation code 38 with a ParkNYC receipt. Ticky compares the confirmed license plate and parking session with the ticket and asks the user to confirm the zone. A mismatch is explained in the review and blocks the ParkNYC draft. For other supported notices, Ticky helps organize confirmed facts into a statement and provides official resources for finding filing instructions.

The user reviews and files the statement. The demo uses synthetic documents and billing is disabled.

## Team · ihatebusiness

- Khafiz Akylzhna
- Askar Miras
- Bolat Ismail

## Technical overview

The frontend uses Vue, TypeScript, and Vite. The FastAPI backend stores cases in SQLite and uses Gemini for document extraction. Backend rules and templates build the review and statement from confirmed facts. Sources live in the [source registry](knowledge), and case access requires a secret. Users can delete their cases and uploaded files.

See the [API contract](docs/api-contract.md) and [hackathon demo walkthrough](docs/demo-release.md).

## Local setup

Open the repository root in VS Code. Use a PowerShell terminal for the backend:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-p3.txt -r requirements-dev.txt
$env:TICKETCLEAR_DEMO_ACCESS = 'true'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In a second PowerShell terminal, start from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite proxies API requests to port 8000. Manual entry works immediately. To enable automatic recognition, set `GEMINI_API_KEY` in the backend process environment and restart the backend. Keep the key on the server.

To run the backend tests, use `./.venv/Scripts/python.exe -m pytest -q` from `backend`. To build the frontend for production, use `npm run build` from `frontend`.
