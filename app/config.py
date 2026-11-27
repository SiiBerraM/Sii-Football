import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

_db = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'siifootball.db').as_posix()}")
if _db.startswith("postgres://"):
    _db = _db.replace("postgres://", "postgresql://", 1)
if _db.startswith("sqlite:///") and not _db.startswith("sqlite:////"):
    rel = _db[len("sqlite:///"):]
    if not os.path.isabs(rel):
        _db = f"sqlite:///{(BASE_DIR / rel).as_posix()}"
DATABASE_URL = _db

OWNER_NAME = "Berra"
OWNER_EMAIL = "noreply@users.noreply.github.com"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "true").lower() == "true"
DEFAULT_RATE_LIMIT = int(os.getenv("DEFAULT_RATE_LIMIT_PER_MIN", "60"))
STALE_AFTER_HOURS = int(os.getenv("STALE_AFTER_HOURS", "48"))
LATEST_JSON = DATA_DIR / "latest.json"
LATEST_CSV = DATA_DIR / "latest.csv"
CONFIG_DIR = BASE_DIR / "config"
