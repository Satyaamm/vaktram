"""Pytest fixtures for API tests.

These tests do not require a live database — they exercise pure functions and
the FastAPI app surface with dependency overrides where needed.
"""

from __future__ import annotations

import os

# Force a deterministic config before importing app modules.
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only")
os.environ.setdefault("ENCRYPTION_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/vaktram_test")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    from app.main import app as _app
    return _app


@pytest.fixture()
def client(app):
    return TestClient(app)
