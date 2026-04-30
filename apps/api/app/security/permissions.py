"""Permission catalog and RBAC checks.

Permissions are stable strings of the form `<resource>:<action>` so they can
be stored in JSON columns and IdP group mappings without enum churn.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.identity import Role, RoleAssignment, RoleScope
from app.models.team import UserProfile

# Resource:action permissions. Keep in lock-step with seeded system roles.
P_MEETING_READ = "meeting:read"
P_MEETING_WRITE = "meeting:write"
P_MEETING_DELETE = "meeting:delete"
P_MEETING_SHARE = "meeting:share"
P_TRANSCRIPT_EXPORT = "transcript:export"
P_BILLING_MANAGE = "billing:manage"
P_TEAM_MANAGE = "team:manage"
P_SSO_MANAGE = "sso:manage"
P_AUDIT_READ = "audit:read"
P_INTEGRATION_MANAGE = "integration:manage"

ALL_PERMISSIONS: set[str] = {
    P_MEETING_READ, P_MEETING_WRITE, P_MEETING_DELETE, P_MEETING_SHARE,
    P_TRANSCRIPT_EXPORT, P_BILLING_MANAGE, P_TEAM_MANAGE, P_SSO_MANAGE,
    P_AUDIT_READ, P_INTEGRATION_MANAGE,
}


@dataclass(frozen=True)
class SystemRole:
    name: str
    permissions: set[str]


SYSTEM_ROLES: dict[str, SystemRole] = {
    "owner": SystemRole("owner", ALL_PERMISSIONS),
    "admin": SystemRole(
        "admin",
        ALL_PERMISSIONS - {P_BILLING_MANAGE},  # billing reserved to owner
    ),
    "member": SystemRole(
        "member",
        {P_MEETING_READ, P_MEETING_WRITE, P_MEETING_SHARE, P_TRANSCRIPT_EXPORT},
    ),
    "viewer": SystemRole("viewer", {P_MEETING_READ}),
    "auditor": SystemRole("auditor", {P_MEETING_READ, P_AUDIT_READ}),
}


async def user_permissions(
    db: AsyncSession, user_id: uuid.UUID, organization_id: uuid.UUID | None
) -> set[str]:
    """Resolve the union of permissions granted to a user in an org scope.

    Implicit role from UserProfile.role still applies (legacy code), so we
    combine it with explicit RoleAssignment rows.
    """
    perms: set[str] = set()

    # Implicit system role from UserProfile
    user = await db.get(UserProfile, user_id)
    if user and user.role in SYSTEM_ROLES:
        perms |= SYSTEM_ROLES[user.role].permissions

    # Explicit assignments
    rows = await db.execute(
        select(Role.permissions)
        .join(RoleAssignment, RoleAssignment.role_id == Role.id)
        .where(RoleAssignment.user_id == user_id)
        .where(
            (RoleAssignment.scope == RoleScope.organization)
            & (RoleAssignment.scope_id == organization_id)
            | (RoleAssignment.scope_id == organization_id)
        )
    )
    for (granted,) in rows.all():
        perms |= set(granted or [])

    return perms


def require_permission(*needed: str):
    """FastAPI dependency: 403 unless the caller has every listed permission."""

    async def _checker(
        user: UserProfile = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        granted = await user_permissions(db, user.id, user.organization_id)
        missing = [p for p in needed if p not in granted]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "missing_permissions", "missing": missing},
            )

    return _checker
