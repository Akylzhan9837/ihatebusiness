from contextlib import contextmanager
from contextlib import closing
from datetime import UTC, datetime
from hashlib import sha256
from hmac import compare_digest
from pathlib import Path
from secrets import token_urlsafe
import sqlite3
from uuid import UUID, uuid4

from app.api.errors import ApiError
from app.models import Case, CaseAccess, Document, JurisdictionState, Offer, TicketFields


def now() -> datetime:
    return datetime.now(UTC)


def unavailable_case() -> ApiError:
    return ApiError(404, "case_not_found", "This case could not be opened. Check your private link.")


class Store:
    def __init__(self, path: Path, offer: Offer):
        self.path = path
        self.offer = offer

    @contextmanager
    def connect(self):
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA secure_delete=ON")
            yield db

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY,
                    secret_hash BLOB NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 0,
                    state TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                    content BLOB NOT NULL
                );
            """)

    def create(self, jurisdiction_state: JurisdictionState | None = None) -> CaseAccess:
        case_id = uuid4()
        secret = token_urlsafe(32)
        timestamp = now()
        case = Case(
            case_id=case_id, offer=self.offer, created_at=timestamp, updated_at=timestamp,
            confirmed_fields=TicketFields(jurisdiction_state=jurisdiction_state),
        )
        with self.connect() as db:
            db.execute("INSERT INTO cases (id, secret_hash, state) VALUES (?, ?, ?)",
                       (str(case_id), sha256(secret.encode()).digest(), case.model_dump_json()))
        return CaseAccess(case_id=case_id, access_secret=secret)

    def open(self, case_id: UUID, token: str) -> tuple[Case, int]:
        with self.connect() as db:
            row = db.execute("SELECT * FROM cases WHERE id=?", (str(case_id),)).fetchone()
        digest = sha256(token.encode()).digest()
        expected = row["secret_hash"] if row is not None else bytes(32)
        if not compare_digest(digest, expected) or row is None:
            raise unavailable_case()
        case = Case.model_validate_json(row["state"])
        case.offer = self.offer
        return case, row["revision"]

    def save(self, case: Case, revision: int, upload: tuple[Document, bytes] | None = None):
        case.updated_at = now()
        with self.connect() as db:
            result = db.execute(
                "UPDATE cases SET state=?, revision=revision+1 WHERE id=? AND revision=?",
                (case.model_dump_json(), str(case.case_id), revision),
            )
            if result.rowcount != 1:
                raise ApiError(409, "case_changed", "The case changed. Reload it and try again.", retryable=True)
            if upload is not None:
                document, content = upload
                db.execute("INSERT INTO documents VALUES (?, ?, ?)",
                           (str(document.document_id), str(case.case_id), content))

    def file(self, case_id: UUID, document_id: UUID) -> bytes:
        with self.connect() as db:
            row = db.execute("SELECT content FROM documents WHERE case_id=? AND id=?",
                             (str(case_id), str(document_id))).fetchone()
        if row is None:
            raise ApiError(409, "document_unavailable", "The document is no longer available.")
        return row["content"]

    def delete(self, case_id: UUID):
        with self.connect() as db:
            db.execute("DELETE FROM cases WHERE id=?", (str(case_id),))
