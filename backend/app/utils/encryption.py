"""
Encryption utilities for securely storing sensitive data like TTLock credentials
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class CredentialEncryption:
    """Handles encryption and decryption of sensitive credentials"""

    def __init__(self):
        self.encryption_key = self._get_or_create_key()

    def _get_or_create_key(self):
        """Get encryption key from environment or generate one"""
        # Use a combination of secret key and salt for encryption
        secret_key = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
        salt = os.getenv('ENCRYPTION_SALT', 'hostify-ttlock-salt').encode()

        # Derive encryption key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        if not data:
            return None
        try:
            encrypted_data = self.encryption_key.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            return None

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded encrypted data and return original string"""
        if not encrypted_data:
            return None
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.encryption_key.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return None

# Global instance
credential_encryption = CredentialEncryption()