"""
Settings for the backend.

Everything is read from ONE .env file in the project root (the same file the
frontend and the data scripts use). Every value is optional: the app runs
without any of them, only sign-in / admin features stay switched off.
"""

import base64
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # gisproject/
DATA_DIR = ROOT / "output"                           # made by scripts/fetch_chamoli_data.py
STORAGE_DIR = ROOT / "backend" / "storage"           # SQLite database + uploaded photos
UPLOAD_DIR = STORAGE_DIR / "uploads"
DB_PATH = STORAGE_DIR / "safeyatra.db"


def load_dotenv(path):
    """Tiny KEY=VALUE reader (same idea as in fetch_chamoli_data.py)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(ROOT / ".env")


def clerk_jwks_url():
    """Where Clerk publishes the public keys used to check sign-in tokens.

    Set CLERK_JWKS_URL directly, or leave it empty: the URL is then worked out
    from the publishable key (pk_test_<base64 of the Clerk frontend domain>).
    """
    if os.environ.get("CLERK_JWKS_URL"):
        return os.environ["CLERK_JWKS_URL"]
    pk = os.environ.get("VITE_CLERK_PUBLISHABLE_KEY", "")
    try:
        encoded = pk.split("_", 2)[2]
        domain = base64.b64decode(encoded + "=" * (-len(encoded) % 4)).decode().rstrip("$")
        return f"https://{domain}/.well-known/jwks.json" if domain else None
    except (IndexError, ValueError, UnicodeDecodeError):
        return None


def _list(name, default=""):
    # "or default": a blank line like CORS_ORIGINS= in .env keeps the default
    return [x.strip() for x in (os.environ.get(name) or default).split(",") if x.strip()]


CLERK_JWKS_URL = clerk_jwks_url()
# Clerk user ids (user_...) that may use the admin panel
ADMIN_USER_IDS = set(_list("ADMIN_USER_IDS"))
# Frontend addresses allowed to call the API (Vite dev server by default)
CORS_ORIGINS = _list("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
WEATHER_REFRESH_MIN = int(os.environ.get("WEATHER_REFRESH_MIN") or 60)
USER_AGENT = "SafeYatra/0.1 (student project" + (
    f"; {os.environ['CONTACT_EMAIL']})" if os.environ.get("CONTACT_EMAIL") else ")")
