"""Smoke tests for the FastAPI surface that don't need a database."""

from __future__ import annotations


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_openapi_schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert schema["info"]["title"]
    # Auth endpoints registered
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/auth/signup" in schema["paths"]


def test_protected_endpoint_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_invalid_bearer_rejected(client):
    r = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert r.status_code == 401
