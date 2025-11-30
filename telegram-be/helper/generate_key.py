#!/usr/bin/env python3
"""Utility script to generate encryption key for .env file."""

from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("Generated Encryption Key:")
    print(key.decode())
    print("\nAdd this to your .env file as:")
    print(f"ENCRYPTION_KEY={key.decode()}")
