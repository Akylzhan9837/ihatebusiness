# Ticky · frontend

Vue 3 + TypeScript + Vite. Весь английский пользовательский путь по `../docs/api-contract.md`.

```bash
npm install
cp .env.example .env        # VITE_API_PROXY=http://localhost:8000
npm run typecheck && npm run build
npm run dev                 # http://localhost:5173, /api проксируется на backend
```

Dev без backend-модулей правил/PDF: `VITE_USE_MOCK=true` в `.env` (только dev, в production вырезается; баннер DEV MOCK виден).

## Маршруты

`/` лендинг → `/new` выбор штата + загрузка/ручной ввод → `/case/{id}/details` → `/receipt` (ParkNYC) или сразу `/report` → `/draft`.
Ссылка на дело: `/case/{id}#key={access_secret}`. Ключ читается один раз (`main.ts`), фрагмент убирается через
`history.replaceState`, ключ лежит в `sessionStorage` вкладки и уходит только заголовком `Authorization: Bearer`.

## Приёмка с реальным API

1. Backend: `TICKETCLEAR_DEMO_ACCESS=true`, `GET /api/ready` отвечает 200 (нужны `app.rules`, `app.export`, ключ AI).
2. `/new` → выбрать штат → подтвердить предупреждение → загрузить синтетический ticket (виден прогресс) → подтвердить поля.
3. Оплата ParkNYC → квитанция + детали сессии → отчёт (факты, источники) → Use demo access → редактор → Save → Copy → Download PDF.
4. «Copy private link» в блоке *Save your private link* → открыть ссылку в приватном окне → `/case/{id}/draft` показывает сохранённый черновик.
