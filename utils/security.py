import os
from cryptography.fernet import Fernet


def get_fernet():
    key = os.getenv("FERNET_SECRET_KEY")

    if key is None:
        raise ValueError("FERNET_SECRET_KEY not set")

    return Fernet(key.encode())

def encrypt_key(api_key):
    fernet = get_fernet()
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_key(encrypted_key):
    fernet = get_fernet()
    return fernet.decrypt(encrypted_key.encode()).decode()