"""Encryption utilities for session strings."""
from cryptography.fernet import Fernet
from src.config import config  # This import still works with our new structure!


class Encryptor:
    """Handle encryption and decryption of sensitive data."""
    
    def __init__(self):
        """Initialize encryptor with key from config."""
        self.fernet = Fernet(config.ENCRYPTION_KEY.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        encrypted_bytes = self.fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a string.
        
        Args:
            encrypted: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        decrypted_bytes = self.fernet.decrypt(encrypted.encode())
        return decrypted_bytes.decode()


encryptor = Encryptor()