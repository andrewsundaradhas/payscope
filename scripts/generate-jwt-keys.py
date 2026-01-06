#!/usr/bin/env python3
"""
Generate RSA keypair for JWT signing/verification.
Uses Python cryptography library (no OpenSSL required).
"""

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_jwt_keypair(private_key_path: str = "jwt_private.pem", public_key_path: str = "jwt_public.pem", key_size: int = 4096):
    """Generate RSA keypair for JWT."""
    
    print(f"Generating {key_size}-bit RSA keypair...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Write keys to files
    private_path = Path(private_key_path)
    public_path = Path(public_key_path)
    
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    
    # Set restrictive permissions (Unix-like, ignored on Windows)
    try:
        private_path.chmod(0o600)
        public_path.chmod(0o644)
    except (AttributeError, NotImplementedError):
        # Windows doesn't support chmod, that's fine
        pass
    
    print(f"[OK] Private key written to: {private_path.absolute()}")
    print(f"[OK] Public key written to: {public_path.absolute()}")
    print("")
    print("[WARNING] SECURITY: Keep the private key secure and never commit it to version control!")
    print("")
    
    return private_path, public_path

if __name__ == "__main__":
    import sys
    
    # Default paths
    private_key = "jwt_private.pem"
    public_key = "jwt_public.pem"
    
    # Allow custom paths via command line
    if len(sys.argv) >= 2:
        private_key = sys.argv[1]
    if len(sys.argv) >= 3:
        public_key = sys.argv[2]
    
    try:
        generate_jwt_keypair(private_key, public_key)
        print("[OK] Keypair generation successful!")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error generating keypair: {e}", file=sys.stderr)
        sys.exit(1)

