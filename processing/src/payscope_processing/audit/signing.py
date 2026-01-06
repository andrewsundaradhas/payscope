from __future__ import annotations

from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


@dataclass(frozen=True)
class Keypair:
    private_key_pem: bytes
    public_key_pem: bytes


def generate_ed25519_keypair() -> Keypair:
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return Keypair(private_key_pem=priv_pem, public_key_pem=pub_pem)


def sign(private_key_pem: bytes, message: bytes) -> bytes:
    priv = serialization.load_pem_private_key(private_key_pem, password=None)
    assert isinstance(priv, Ed25519PrivateKey)
    return priv.sign(message)


def verify(public_key_pem: bytes, message: bytes, signature: bytes) -> bool:
    pub = serialization.load_pem_public_key(public_key_pem)
    assert isinstance(pub, Ed25519PublicKey)
    try:
        pub.verify(signature, message)
        return True
    except Exception:
        return False




