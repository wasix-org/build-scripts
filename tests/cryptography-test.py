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

def test_key_derivation():
    password = b"password"
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    assert isinstance(key, bytes) and len(key) == 44
    print("[✓] Key derivation (PBKDF2HMAC) test passed.")

def test_asymmetric_encryption():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    message = b"Encrypt me!"
    ciphertext = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    assert plaintext == message
    print("[✓] Asymmetric encryption (RSA) test passed.")

if __name__ == "__main__":
    test_symmetric_encryption()
    test_hashing()
    test_key_derivation()
    test_asymmetric_encryption()
