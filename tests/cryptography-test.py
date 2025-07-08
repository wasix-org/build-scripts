import os
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding

def test_symmetric_encryption():
    key = Fernet.generate_key()
    f = Fernet(key)
    message = b"Secret Message"
    token = f.encrypt(message)
    decrypted = f.decrypt(token)
    assert decrypted == message
    print("[✓] Symmetric encryption (Fernet) test passed.")

def test_hashing():
    digest = hashes.Hash(hashes.SHA256())
    data = b"important data"
    digest.update(data)
    hash_result = digest.finalize()
    assert isinstance(hash_result, bytes) and len(hash_result) == 32
    print("[✓] Hashing (SHA256) test passed.")

if __name__ == "__main__":
    test_symmetric_encryption()
    test_hashing()
