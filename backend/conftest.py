"""
Root conftest — sets environment variables BEFORE any app module is imported.
Also patches startup side-effects that would fail without real infrastructure.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret-for-pytest-hs256")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(scope="session", autouse=True)
def patch_startup():
    """Prevent real DB seed and background scheduler from starting during tests."""
    mock_scheduler = MagicMock()
    mock_scheduler.return_value.add_job = MagicMock()
    mock_scheduler.return_value.start = MagicMock()

    with (
        patch("app.main._seed_initial_data", new=AsyncMock(return_value=None)),
        patch("app.main.BackgroundScheduler", mock_scheduler),
    ):
        yield
