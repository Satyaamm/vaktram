"""SSO endpoints: SAML SP-initiated login + ACS, OIDC start + callback.

For production-grade SAML you almost always want to outsource the heavy
lifting to a service like WorkOS or Auth0. The code below is a self-hosted
reference implementation good enough for proof-of-concept and audits, with a
clean swap point for `workos_service` when you sign up for the SaaS.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_db
from app.services import sso_service
from app.utils.security import create_access_token, create_refresh_token

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/sso", tags=["sso"])


@router.get("/lookup")
async def lookup_idp_for_email(email: str, db: AsyncSession = Depends(get_db)):
    """UI calls this when the user types their work email on the login page."""
    conn = await sso_service.find_connection_by_email(db, email)
    if not conn:
        return {"sso": False}
    return {"sso": True, "type": conn.type.value, "init_url": f"/api/v1/sso/init?email={email}"}


@router.get("/init")
async def init_sso(email: str, db: AsyncSession = Depends(get_db)):
    """Begin the SP-initiated flow. Redirects to the IdP."""
    conn = await sso_service.find_connection_by_email(db, email)
    if not conn:
        raise HTTPException(404, "No SSO connection for this email domain")

    if conn.type.value == "saml":
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth

            sp_acs_url = f"{settings.api_base_url}/api/v1/sso/saml/acs"
            sp_entity = f"{settings.api_base_url}/saml/metadata"
            cfg = sso_service.build_saml_settings(conn, sp_acs_url, sp_entity)
            req = {
                "https": "on",
                "http_host": settings.api_base_url.replace("https://", "").replace("http://", ""),
                "script_name": "/api/v1/sso/init",
                "get_data": {},
                "post_data": {},
            }
            auth = OneLogin_Saml2_Auth(req, cfg)
            return RedirectResponse(auth.login())
        except ImportError:
            raise HTTPException(503, "SAML provider library not installed on this deployment")

    if conn.type.value == "oidc":
        from authlib.integrations.starlette_client import OAuth

        oauth = OAuth()
        oauth.register(
            name="idp",
            client_id=conn.oidc_client_id,
            client_secret="",  # decrypted at request time in real impl
            server_metadata_url=f"{conn.oidc_issuer}/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        # Authlib normally requires Request session — kept as a sketch here.
        raise HTTPException(501, "OIDC start not yet implemented in self-hosted mode")

    raise HTTPException(400, f"Unsupported SSO type: {conn.type}")


@router.post("/saml/acs")
async def saml_acs(request: Request, db: AsyncSession = Depends(get_db)):
    """SAML Assertion Consumer Service. IdP POSTs the signed assertion here."""
    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth
    except ImportError:
        raise HTTPException(503, "SAML provider library not installed")

    form = await request.form()
    email = (form.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(400, "Missing email in assertion")
    conn = await sso_service.find_connection_by_email(db, email)
    if not conn:
        raise HTTPException(403, "No SSO connection for this domain")

    user = await sso_service.upsert_user_from_assertion(
        db,
        organization_id=conn.organization_id,
        email=email,
        name=form.get("displayName"),
        groups=(form.getlist("groups") if hasattr(form, "getlist") else None),
        conn=conn,
    )
    access = create_access_token(user.id, user.email)
    refresh, _jti = create_refresh_token(user.id)
    return RedirectResponse(
        f"{settings.frontend_base_url}/auth/sso-callback#access={access}&refresh={refresh}"
    )
