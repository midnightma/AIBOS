import os
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import base64
import json

class CryptoEngine:
    @staticmethod
    def generate_ed25519_keypair():
        priv = ed25519.Ed25519PrivateKey.generate()
        pub = priv.public_key()
        return priv, pub

    @staticmethod
    def generate_x25519_keypair():
        priv = x25519.X25519PrivateKey.generate()
        pub = priv.public_key()
        return priv, pub

    @staticmethod
    def derive_symmetric_key(local_priv_x, remote_pub_x):
        shared_key = local_priv_x.exchange(remote_pub_x)
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'AIBOS_V1_KEY_EXCHANGE')
        return hkdf.derive(shared_key)

    @staticmethod
    def encrypt_payload(payload_dict: dict, symmetric_key: bytes) -> tuple:
        aesgcm = AESGCM(symmetric_key)
        nonce = os.urandom(12)
        data = json.dumps(payload_dict).encode('utf-8')
        ciphertext = aesgcm.encrypt(nonce, data, None)
        # AESGCM appends the 16-byte tag to the ciphertext
        return nonce, ciphertext

    @staticmethod
    def decrypt_payload(nonce: bytes, ciphertext: bytes, symmetric_key: bytes) -> dict:
        aesgcm = AESGCM(symmetric_key)
        data = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(data.decode('utf-8'))

    @staticmethod
    def sign_message(priv_key: ed25519.Ed25519PrivateKey, data: bytes) -> bytes:
        return priv_key.sign(data)

    @staticmethod
    def verify_signature(pub_key: ed25519.Ed25519PublicKey, signature: bytes, data: bytes) -> bool:
        try:
            pub_key.verify(signature, data)
            return True
        except Exception:
            return False