# Ticky

Ticky helps users understand a U.S. civil or traffic notice and prepare a factual statement. The demo accepts synthetic documents.

The public workflow starts with a state selection, then takes the user through ticket details, review, and an editable PDF draft. NYC Department of Finance code 38 with ParkNYC evidence also has a dedicated rules check. Other notices receive a factual statement and official resources for checking where and how to file.

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

The workflow and API are documented in [the API contract](docs/api-contract.md). The case data is stored in SQLite, and the source registry is in [knowledge](knowledge).
