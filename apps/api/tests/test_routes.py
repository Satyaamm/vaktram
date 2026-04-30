"""Surface-level route checks that don't need a database.

We just verify each new router is mounted and that protected routes return
401 when called without a token. Schema regressions show up here too via
the OpenAPI doc.
"""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "path,method,expected",
    [
        ("/api/v1/billing/plans", "GET", 200),  # public
        ("/api/v1/billing/subscription", "GET", 401),
        ("/api/v1/ask/threads", "GET", 401),
        ("/api/v1/topics", "GET", 401),
        ("/api/v1/channels", "GET", 401),
        ("/api/v1/compliance/audit", "GET", 401),
        ("/api/v1/scim/v2/Users", "GET", 401),
    ],
)
def test_route_auth_or_public(client, path, method, expected):
    resp = client.request(method, path)
    assert resp.status_code == expected, f"{method} {path} -> {resp.status_code}"


def test_billing_plans_shape(client):
    resp = client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    plans = resp.json()
    for tier in ("free", "pro", "team", "business", "enterprise"):
        assert tier in plans, f"missing tier {tier}"
        p = plans[tier]
        assert "name" in p and "limits" in p and "features" in p


def test_openapi_lists_all_new_routes(client):
    schema = client.get("/openapi.json").json()
    paths = set(schema["paths"].keys())
    expected = {
        "/api/v1/auth/signup",
        "/api/v1/billing/plans",
        "/api/v1/ask/threads",
        "/api/v1/topics",
        "/api/v1/channels",
        "/api/v1/soundbites",
        "/api/v1/compliance/audit",
        "/api/v1/sso/lookup",
        "/api/v1/scim/v2/Users",
    }
    missing = expected - paths
    assert not missing, f"missing routes in OpenAPI: {missing}"


def test_soundbite_share_route_exists(client):
    """The public share path must be registered (we'd 401 on auth-required
    routes; this is unauthenticated, so it must hit the handler)."""
    schema = client.get("/openapi.json").json()
    assert any(
        p.startswith("/api/v1/soundbites/shared/") for p in schema["paths"]
    ), "public soundbite share route is not mounted"
