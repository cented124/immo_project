import hashlib, hmac, os
from argon2 import PasswordHasher
from cryptography.fernet import Fernet
from .db import DATA

hasher = PasswordHasher()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def key_material():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        p = DATA / "encryption.key"
        if not p.exists():
            try:
                fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as f:
                    f.write(Fernet.generate_key())
            except FileExistsError:
                pass
        key = p.read_bytes()
    return key.encode() if isinstance(key, str) else key


def cipher():
    return Fernet(key_material())


def document_token(submission_key):
    return hmac.new(
        key_material(), ("document-return:" + submission_key).encode(), hashlib.sha256
    ).hexdigest()


def encrypt(value):
    return cipher().encrypt(value.encode()).decode() if value else ""


def decrypt(value):
    return cipher().decrypt(value.encode()).decode() if value else ""
