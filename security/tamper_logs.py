import hashlib
import json
import time
from storage.database import get_db_connection
from security.crypto_engine import CryptoEngine

class TamperEvidentLog:
    @staticmethod
    def append_log(event_type: str, data: dict, local_ed_priv: bytes):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get previous hash
        cursor.execute("SELECT prev_hash, encrypted_blob FROM secure_logs ORDER BY log_id DESC LIMIT 1")
        last_log = cursor.fetchone()
        
        if last_log:
            prev_hash = hashlib.sha256(last_log['encrypted_blob'] + last_log['prev_hash'].encode('utf-8')).hexdigest()
        else:
            prev_hash = hashlib.sha256(b"GENESIS").hexdigest()
        
        timestamp = int(time.time())
        data['timestamp'] = timestamp
        
        # In a real military system, this blob is encrypted with a log-specific pubkey.
        # Here we serialize for tamper evidence.
        blob = json.dumps(data, sort_keys=True).encode('utf-8')
        
        from cryptography.hazmat.primitives.asymmetric import ed25519
        priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(local_ed_priv)
        
        signature = CryptoEngine.sign_message(priv_key, blob + prev_hash.encode('utf-8'))
        
        cursor.execute(
            "INSERT INTO secure_logs (timestamp, event_type, encrypted_blob, prev_hash, signature) VALUES (?, ?, ?, ?, ?)",
            (timestamp, event_type, blob, prev_hash, signature)
        )
        conn.commit()