import json
import os
import uuid
import base64
from config import TRANSFERS_DIR
from security.crypto_engine import CryptoEngine
from cryptography.hazmat.primitives.asymmetric import ed25519

class OfflinePackager:
    @staticmethod
    def create_package(destination_id: str, sender_id: str, payload: dict, symmetric_key: bytes, priv_key: ed25519.Ed25519PrivateKey) -> str:
        msg_id = str(uuid.uuid4())
        nonce, ciphertext = CryptoEngine.encrypt_payload(payload, symmetric_key)
        
        # In AESGCM from cryptography, the tag is the last 16 bytes of the ciphertext
        actual_ciphertext = ciphertext[:-16]
        tag = ciphertext[-16:]
        
        header = {
            "sender_id": sender_id,
            "destination_id": destination_id,
            "message_id": msg_id,
            "timestamp": int(os.time() if hasattr(os, 'time') else __import__('time').time()),
            "nonce": base64.b64encode(nonce).decode('utf-8')
        }
        
        signature_data = json.dumps(header, sort_keys=True).encode('utf-8') + actual_ciphertext + tag
        signature = CryptoEngine.sign_message(priv_key, signature_data)
        
        package = {
            "header": header,
            "ciphertext": base64.b64encode(actual_ciphertext).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8'),
            "signature": base64.b64encode(signature).decode('utf-8')
        }
        
        filename = os.path.join(TRANSFERS_DIR, f"mission_{msg_id}.aibos")
        with open(filename, "w") as f:
            json.dump(package, f)
            
        return filename

    @staticmethod
    def parse_package(filepath: str, symmetric_key: bytes, pub_key: ed25519.Ed25519PublicKey) -> dict:
        with open(filepath, "r") as f:
            package = json.load(f)
            
        header = package["header"]
        actual_ciphertext = base64.b64decode(package["ciphertext"])
        tag = base64.b64decode(package["tag"])
        signature = base64.b64decode(package["signature"])
        nonce = base64.b64decode(header["nonce"])
        
        signature_data = json.dumps(header, sort_keys=True).encode('utf-8') + actual_ciphertext + tag
        
        if not CryptoEngine.verify_signature(pub_key, signature, signature_data):
            raise ValueError("Invalid package signature. Tampering detected.")
            
        full_ciphertext = actual_ciphertext + tag
        payload = CryptoEngine.decrypt_payload(nonce, full_ciphertext, symmetric_key)
        
        return {
            "header": header,
            "payload": payload
        }