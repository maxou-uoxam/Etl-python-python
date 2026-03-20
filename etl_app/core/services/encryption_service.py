"""Encryption service for securing connection passwords."""
import base64
import hashlib
from cryptography.fernet import Fernet
from etl_app.config import settings


class EncryptionService:
    def __init__(self):
        # Derive a valid 32-byte Fernet key from the configured secret
        raw = settings.connection_encryption_key.encode()
        key_bytes = hashlib.sha256(raw).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes))

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ""
