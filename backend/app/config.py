from dataclasses import dataclass
from os import getenv
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db: Path
    origins: tuple[str, ...] = ()
    demo_access: bool = False
    ai_key: str = ""
    ai_model: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db=Path(getenv("TICKETCLEAR_DB", "./data/ticketclear.sqlite3")),
            origins=tuple(
                origin.strip()
                for origin in getenv("TICKETCLEAR_CORS_ORIGINS", "").split(",")
                if origin.strip() and origin.strip() != "*"
            ),
            demo_access=getenv("TICKETCLEAR_DEMO_ACCESS", "false").lower() == "true",
            ai_key=getenv("OPENAI_API_KEY", "").strip(),
            ai_model=getenv("OPENAI_MODEL", "").strip(),
        )
