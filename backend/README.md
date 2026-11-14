# TicketClear · backend

Требуется Python 3.11+. Выполняйте из папки backend.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:TICKETCLEAR_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
$env:TICKETCLEAR_DEMO_ACCESS = "true"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Проверки: `GET /api/health`, `GET /api/ready`, OpenAPI на `/docs`. Backend-тесты: `python -m pytest -q`. Тестовый evaluator и PDF-генератор передаются через фабрику приложения в тестах.

Переменные запуска:

- `GEMINI_API_KEY` — секрет на сервере, задаётся в окружении или настройках хостинга.
- `GEMINI_MODEL` — модель Gemini, по умолчанию gemini-3.5-flash-lite. Используйте проект Free без Billing. При исчерпании квоты возвращается 429.
- `TICKETCLEAR_DB` — путь к SQLite на постоянном диске, по умолчанию `./data/ticketclear.sqlite3`.
- `TICKETCLEAR_CORS_ORIGINS` — origins фронтенда через запятую. При общем origin можно оставить пустой.
- `TICKETCLEAR_DEMO_ACCESS=true` — включить отдельный доступ к подготовке черновика без списания.

Контракт в `../docs/api-contract.md`. Правила `app.rules.evaluate` и PDF `app.export.render_pdf` подхватываются при запуске. Полный сценарий требует оба модуля и настройку AI. Без ключа можно создать дело, загрузить файл и перейти к ручному вводу. В публичном демо загружайте только синтетические документы.
