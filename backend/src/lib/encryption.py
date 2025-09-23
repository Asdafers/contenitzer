"""
Encryption utilities for sensitive data storage (API keys, user data).
"""
import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Encryption configuration
ENCRYPTION_KEY_ENV = "CONTENTIZER_ENCRYPTION_KEY"
SALT_ENV = "CONTENTIZER_ENCRYPTION_SALT"

class EncryptionError(Exception):
    """Custom exception for encryption operations"""
    pass

class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""

    def __init__(self):
        """Initialize encryption service with key derivation"""
        self._fernet = None
        self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize Fernet encryption with derived key"""
        try:
            # Get or generate encryption key and salt
            encryption_key = os.getenv(ENCRYPTION_KEY_ENV)
            salt = os.getenv(SALT_ENV)

            if not encryption_key:
                # Generate a new key for development - in production this should be set
                encryption_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
                logger.warning(f"No encryption key found in {ENCRYPTION_KEY_ENV}, generated temporary key")

            if not salt:
                # Generate salt for development
                salt = base64.urlsafe_b64encode(os.urandom(16)).decode()
                logger.warning(f"No salt found in {SALT_ENV}, generated temporary salt")

            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            self._fernet = Fernet(key)

            logger.info("Encryption service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")

    def encrypt(self, data: str) -> str:
        """
        Encrypt string data and return base64 encoded result

        Args:
            data: String to encrypt

        Returns:
            Base64 encoded encrypted string

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            if not data:
                return data

            encrypted_bytes = self._fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt base64 encoded encrypted data

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted string

        Raises:
            EncryptionError: If decryption fails
        """
        try:
            if not encrypted_data:
                return encrypted_data

            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")

    def is_encrypted(self, data: str) -> bool:
        """
        Check if data appears to be encrypted (base64 format check)

        Args:
            data: String to check

        Returns:
            True if data appears encrypted, False otherwise
        """
        try:
            if not data:
                return False

            # Try to base64 decode - encrypted data should be base64 encoded
            base64.urlsafe_b64decode(data.encode('utf-8'))
            return True

        except Exception:
            return False

# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None

def get_encryption_service() -> EncryptionService:
    """Get global encryption service instance"""
    global _encryption_service

    if _encryption_service is None:
        _encryption_service = EncryptionService()

    return _encryption_service

def encrypt_api_key(api_key: str) -> str:
    """
    Convenience function to encrypt API keys

    Args:
        api_key: API key to encrypt

    Returns:
        Encrypted API key
    """
    return get_encryption_service().encrypt(api_key)

def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    Convenience function to decrypt API keys

    Args:
        encrypted_api_key: Encrypted API key

    Returns:
        Decrypted API key
    """
    return get_encryption_service().decrypt(encrypted_api_key)

def ensure_api_key_encrypted(api_key: str) -> str:
    """
    Ensure API key is encrypted, only encrypting if not already encrypted

    Args:
        api_key: API key that may or may not be encrypted

    Returns:
        Encrypted API key
    """
    service = get_encryption_service()

    if service.is_encrypted(api_key):
        return api_key
    else:
        return service.encrypt(api_key)

def ensure_api_key_decrypted(api_key: str) -> str:
    """
    Ensure API key is decrypted, only decrypting if encrypted

    Args:
        api_key: API key that may or may not be encrypted

    Returns:
        Decrypted API key
    """
    service = get_encryption_service()

    if service.is_encrypted(api_key):
        return service.decrypt(api_key)
    else:
        return api_key