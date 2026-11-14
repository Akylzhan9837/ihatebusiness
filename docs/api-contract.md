# TicketClear API · v1

## Расширенный приём штрафов Ticky

Новые клиенты передают `jurisdiction_state` при создании дела. Доступны 50 штатов и DC. В `confirmed_fields` также появились `jurisdiction_state` и `ticket_type` (`parking`, `camera`, `moving`, `other_civil`, `unknown`). Номера уведомлений и коды нарушений — строки до 64 символов. Для сценария ParkNYC по-прежнему нужен десятизначный номер. Старые дела без этих полей сохраняют прежний маршрут.

Для остальных гражданских штрафов `POST /analyze` возвращает официальные ресурсы и проверяет, есть ли ведомство, номер, подтверждённый тип и пояснение пользователя. Если данных достаточно, `draft_kind: "factual"` означает, что будет подготовлено заявление по словам пользователя. Применимые основания, сроки и возможность подачи в конкретном деле требуют отдельной проверки. Ссылки хранятся в `knowledge/citation-sources.json`.

## Сценарий и команды

Один тип дела: NYC Department of Finance, violation code 38 (failure to display), с оплатой через ParkNYC. Проверяем совпадение номера и штата, зоны/места и интервала парковки с подтверждённым штрафом. Бумажные квитанции, льготный интервал и другие коды выходят за границы этого сценария. Основание для проверки — описание [кода 38 NYC DOF](https://www.nyc.gov/site/finance/vehicles/services-violation-codes.page) и [инструкция NYC DOT об оплате через ParkNYC](https://www.nyc.gov/html/dot/html/motorist/parking-rates.shtml). Для самостоятельной подачи — [NYC DOF Dispute a Ticket](https://www.nyc.gov/site/finance/vehicles/dispute-a-ticket.page). MVP не вычисляет персональный срок.

- Участник 1, `feature/backend-ai`: FastAPI, SQLite, доступ к делу, хранение, извлечение, подтверждение, интерфейсы правил и экспорта, генерация текста и backend-тесты.
- Участник 2, `feature/frontend`: весь `frontend/` и англоязычный браузерный путь.
- Участник 3, `feature/rules-qa`: `backend/app/rules/`, `backend/app/export/`, `knowledge/`, `fixtures/`, `tests/e2e/`, `docs/` кроме первого коммита контракта, публичный запуск.

## HTTP

Дела используют UUID. Все операции с ID требуют `Authorization: Bearer <access_secret>`. Создание возвращает секрет единожды. Ссылку для повторного открытия frontend формирует как `/case/{case_id}#key={access_secret}`: прочитать фрагмент, убрать через history.replaceState, держать ключ в памяти вкладки или sessionStorage, отправлять только заголовком. Не передавать ключ в query, аналитику или логи. Ошибка доступа и неизвестный ID дают одинаковый 404. Ответы API используют `Cache-Control: no-store`.

| Метод и адрес | Запрос | Ответ |
| --- | --- | --- |
| POST /api/cases | `{"synthetic_only":true}` | 201, `{case_id, access_secret}` |
| GET /api/cases/{id} | — | `Case` |
| POST /api/cases/{id}/documents | multipart `kind` = `ticket\|evidence`, `file` | 201, `{document_id, kind, filename, media_type, size_bytes}` |
| POST /api/cases/{id}/extract | — | `{fields, warnings}` |
| PATCH /api/cases/{id} | `{confirmed_fields?, circumstances?, answers?, outcome?}` | обновлённый `Case` |
| POST /api/cases/{id}/analyze | — | `Analysis` |
| POST /api/cases/{id}/draft | `{"demo_access":true}` | `Draft` |
| PATCH /api/cases/{id}/draft | `{"text":"…"}` | обновлённый `Draft` |
| GET /api/cases/{id}/export | — | PDF, `Content-Disposition: attachment` |
| DELETE /api/cases/{id} | — | 204 |

`Case` имеет `case_id, documents, extraction, confirmed_fields, circumstances, answers, outcome, analysis, draft, offer, created_at, updated_at`. До сохранения `extraction, analysis, draft, outcome` равны null. `offer` содержит `{price_cents:1900,currency:"USD",mode:"demo"|"unavailable",charge:false}`. Используйте `demo_access:true` после явного клика *Use demo access* при `mode:"demo"`. Это отдельный доступ без списания. Любой анализирующий вход — подтверждённые поля, обстоятельства, структурированные ответы, новые файлы — при изменении сбрасывает предыдущий анализ и делает текущий черновик устаревшим. Повторный POST draft возвращает сохранённый текст, пока анализ актуален. После изменений повторный POST генерирует черновик заново.

### Данные

Каждое поле extraction: `{value:string|null,source_document_id:string,page:number|null,source_text:string|null,needs_confirmation:true}`. Значение OCR и цитату проверяет человек. `warnings` — массив строк. Извлечённые данные никогда автоматически не становятся подтверждёнными. `confirmed_fields` — объект из `ticket_number, issuing_authority, city, violation_code, violation_description, issue_date, issue_time, location, amount, plate_number, plate_state`. Значения — строки или null. Дата YYYY-MM-DD, время HH:MM (локальное NYC), сумма USD как десятичная строка, `ticket_number` — строка из 10 цифр с сохранением ведущих нулей. Канонические значения города и инстанции для UI: `NYC` и `NYC Department of Finance`.

PATCH выполняет merge внутри `confirmed_fields` и `answers`. Явный null у ключа очищает значение. `circumstances` — строка до 4000 символов или null. `outcome` — `submitted|dismissed|upheld|other` или null, это отметка пользователя.

`answers`:
- `payment_method`: `parknyc|other|none|unknown`.
- `evidence_document_id`: UUID загруженной квитанции `kind:evidence` этого дела.
- `session_start`, `session_end`: местные дата и время NYC, формат YYYY-MM-DDTHH:MM, без часового пояса.
- `session_plate_number`, `session_plate_state`: значения из квитанции.
- `session_zone`: шестизначный ParkNYC zone.
- `zone_matches_ticket_location`: boolean, пользователь сверил зону с местом штрафа.
- `receipt_details_confirmed`: boolean, пользователь сверил указанные сведения с приложенным файлом.

Один ticket, до четырёх evidence. PDF/JPEG/PNG до 8 MiB на файл, PDF до пяти страниц, изображение до 16 мегапикселей. Имя во входном multipart игнорируется, API выдаёт безопасное имя. Обратите внимание пользователя на **synthetic documents only** до загрузки. Первичное извлечение отправляет только ticket в серверный AI-адаптер. Сведения о квитанции пользователь вносит вручную.

### Analysis

`{status, summary, findings, missing_information, questions, next_steps, sources, draft_available}`.

Статусы `unsupported`, `needs_information`, `no_supported_ground_identified`, `ready_for_draft`. Последний — единственный статус с `draft_available:true`. `missing_information` и `next_steps` — массивы читаемых строк. Вопрос: `{id, prompt, type, options}`. `type` бывает `choice|text|datetime|boolean|evidence`, `options` — массив `{value,label}`, для остальных типов пустой. `id` соответствует имени ключа в `answers`.

Finding: `{id,title,explanation,supporting_fact_ids,source_ids,limitations,suggested_next_step}`. `limitations` — массив строк, `suggested_next_step` — строка. ID факта: `confirmed_fields.<field>` или `answers.<field>`. Source: `{id,title,url,jurisdiction,topic,accessed_at,relevant_excerpt}`, дата YYYY-MM-DD. Показывайте источники по `source_ids`. Все ссылки приходят из реестра.

### Draft

`{text, attachments, submission_steps, stale, updated_at}`. Приложение: `{document_id, filename}`. Инструкция: `{text, url}` с официальным URL. При устаревшем черновике покажите сохранённый текст для копирования и предложите повторить анализ. Сохранение текста и экспорт доступны после перегенерации актуального черновика.

### Ошибки

`{"error":{"code":"ai_unavailable","message":"…","retryable":true}}`. 404 неизвестное/недоступное дело, 409 конфликт, неполный или устаревший этап, 413 размер, 415 неподдерживаемый формат, 422 невалидный ввод, 429 занято извлечение AI, 503 недоступный AI/правила/экспорт. Обработайте загрузку, пустые поля, непрочитанный файл, повтор и ручной ввод. В ответах 422 нет отражённого пользовательского ввода.

## Python-интеграция для участника 3

`app.rules.evaluate(confirmed_fields: TicketFields, answers: Answers, documents: list[Document]) -> Analysis`, синхронная чистая функция. Типы в `app.models`. Backend отсекает неподдерживаемый город/инстанцию/код и требует подтверждённые номер штрафа, дату, время, место, номер и штат автомобиля до вызова правила. Модуль правил обрабатывает способ оплаты, наличие приложения, достоверность сведений со слов пользователя и совпадения. В findings укажите ограничение ручной сверки. Модуль обращается только к локальному проверенному реестру. Для ready_for_draft включите источник `nyc-dof-dispute` с URL официальной страницы подачи.

`app.export.render_pdf(draft: Draft) -> bytes`, шаблон PDF для текста и списка приложений, без скачивания URL или автоматической подачи. При отсутствии модулей backend отвечает `503 rules_unavailable` / `503 export_unavailable`.

Проверка здоровья: `GET /api/health` (процесс), `GET /api/ready` (готовность конфигурации и установленных модулей для полного сценария, без внешнего запроса к AI).
