"""Unit tests for EncryptionService."""
import pytest
from etl_app.core.services.encryption_service import EncryptionService


class TestEncryptionService:
    def setup_method(self):
        self.svc = EncryptionService()

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "MyS3cretP@ssword!"
        encrypted = self.svc.encrypt(plaintext)
        assert encrypted != plaintext
        assert encrypted != ""
        decrypted = self.svc.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty(self):
        assert self.svc.encrypt("") == ""

    def test_decrypt_empty(self):
        assert self.svc.decrypt("") == ""

    def test_decrypt_invalid_returns_empty(self):
        result = self.svc.decrypt("not-valid-cipher-text")
        assert result == ""

    def test_encrypt_produces_different_ciphertext_each_time(self):
        # Fernet adds random IV, so same plaintext → different ciphertext
        e1 = self.svc.encrypt("password")
        e2 = self.svc.encrypt("password")
        assert e1 != e2
        # But both decrypt correctly
        assert self.svc.decrypt(e1) == "password"
        assert self.svc.decrypt(e2) == "password"
