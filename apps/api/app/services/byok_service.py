"""BYOK / Customer-Managed Keys: envelope encryption.

Default: all secrets and audio at rest are encrypted with the platform key
(via the existing Fernet-based encryption_service). Enterprise tier can opt
to hold the KEK in their own KMS (AWS, GCP, Azure). When an org has a KmsKey
record, every encrypt() generates a per-record DEK, encrypts the DEK with the
customer's KEK, and stores the wrapped DEK alongside the ciphertext. The
platform never sees the customer's KEK material — only the ARN.

This file is the abstraction. The wrapped-DEK payload format is:
   v1:<wrapped_dek_b64>:<ciphertext_b64>
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import KmsKey

logger = logging.getLogger(__name__)


class KmsBackend(Protocol):
    async def wrap(self, key_arn: str, dek: bytes) -> bytes: ...
    async def unwrap(self, key_arn: str, wrapped: bytes) -> bytes: ...


class AwsKmsBackend:
    """boto3-based KMS backend. Lazy import so non-AWS deployments work."""

    async def wrap(self, key_arn: str, dek: bytes) -> bytes:
        import boto3

        client = boto3.client("kms")
        resp = client.encrypt(KeyId=key_arn, Plaintext=dek)
        return resp["CiphertextBlob"]

    async def unwrap(self, key_arn: str, wrapped: bytes) -> bytes:
        import boto3

        client = boto3.client("kms")
        resp = client.decrypt(KeyId=key_arn, CiphertextBlob=wrapped)
        return resp["Plaintext"]


_backends: dict[str, KmsBackend] = {"aws": AwsKmsBackend()}


def _aes_gcm_encrypt(dek: bytes, plaintext: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)
    return nonce + AESGCM(dek).encrypt(nonce, plaintext, None)


def _aes_gcm_decrypt(dek: bytes, blob: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    return AESGCM(dek).decrypt(blob[:12], blob[12:], None)


async def encrypt_for_org(
    db: AsyncSession, organization_id: uuid.UUID, plaintext: bytes
) -> bytes:
    """Return ciphertext using the org's BYOK key, or platform default."""
    key_row = (
        await db.execute(
            select(KmsKey)
            .where(KmsKey.organization_id == organization_id, KmsKey.enabled.is_(True))
        )
    ).scalar_one_or_none()

    if key_row is None:
        from app.services.encryption_service import encrypt as platform_encrypt

        return platform_encrypt(plaintext.decode() if isinstance(plaintext, bytes) else plaintext).encode()

    backend = _backends.get(key_row.provider)
    if backend is None:
        raise RuntimeError(f"Unsupported KMS provider: {key_row.provider}")
    dek = os.urandom(32)
    wrapped = await backend.wrap(key_row.key_arn, dek)
    ct = _aes_gcm_encrypt(dek, plaintext)
    return b"v1:" + base64.b64encode(wrapped) + b":" + base64.b64encode(ct)


async def decrypt_for_org(
    db: AsyncSession, organization_id: uuid.UUID, blob: bytes
) -> bytes:
    if not blob.startswith(b"v1:"):
        from app.services.encryption_service import decrypt as platform_decrypt

        return platform_decrypt(blob.decode()).encode()
    _, wrapped_b64, ct_b64 = blob.split(b":", 2)
    wrapped = base64.b64decode(wrapped_b64)
    ct = base64.b64decode(ct_b64)
    key_row = (
        await db.execute(
            select(KmsKey)
            .where(KmsKey.organization_id == organization_id, KmsKey.enabled.is_(True))
        )
    ).scalar_one_or_none()
    if key_row is None:
        raise RuntimeError("Cannot decrypt BYOK blob without org KMS key")
    backend = _backends[key_row.provider]
    dek = await backend.unwrap(key_row.key_arn, wrapped)
    return _aes_gcm_decrypt(dek, ct)
