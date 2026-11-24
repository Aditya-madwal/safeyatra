import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # backend/

from app import config  # noqa: E402


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    """API client using a throwaway database, with sign-in faked."""
    tmp = tmp_path_factory.mktemp("storage")
    config.STORAGE_DIR, config.UPLOAD_DIR, config.DB_PATH = tmp, tmp / "uploads", tmp / "test.db"
    from fastapi.testclient import TestClient
    from app import main
    from app.auth import admin_user, current_user

    user = {"user_id": "user_test", "is_admin": True}
    main.app.dependency_overrides[current_user] = lambda: user
    main.app.dependency_overrides[admin_user] = lambda: user
    main.weather_loop = _no_weather          # no network calls in tests
    with TestClient(main.app) as c:
        yield c


async def _no_weather():
    return None
