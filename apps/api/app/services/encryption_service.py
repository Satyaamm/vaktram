"""API key encryption using Fernet symmetric encryption."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

settings = get_settings()


class EncryptionService:
    """Encrypt and decrypt sensitive values (API keys, tokens) using Fernet."""

    def __init__(self, key: str | None = None):
        raw_key = key or settings.encryption_key
        if not raw_key:
            raise RuntimeError(
                "ENCRYPTION_KEY must be set. Generate one with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        self._fernet = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)

    def encrypt(self, plaintext: str | None) -> str | None:
        """Encrypt a plaintext string. Returns base64-encoded ciphertext."""
        if plaintext is None:
            return None
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str | None) -> str | None:
        """Decrypt a Fernet-encrypted string."""
        if ciphertext is None:
            return None
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            raise ValueError("Failed to decrypt: invalid token or wrong key")
