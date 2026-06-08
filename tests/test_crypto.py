import pytest
from security.crypto_engine import CryptoEngine
import json
import base64
from cryptography.hazmat.primitives import serialization

def test_ed25519_signatures():
    # Generate Keypair
    priv_key, pub_key = CryptoEngine.generate_ed25519_keypair()
    
    # Sign Data
    message = b"Strictly confidential mission payload."
    signature = CryptoEngine.sign_message(priv_key, message)
    
    # Verify Data
    assert CryptoEngine.verify_signature(pub_key, signature, message) == True
    
    # Tamper with message
    tampered_message = b"Strictly confidential mission payload!"
    assert CryptoEngine.verify_signature(pub_key, signature, tampered_message) == False

def test_x25519_key_exchange_and_aes_gcm():
    # Unit A Keys
    a_priv, a_pub = CryptoEngine.generate_x25519_keypair()
    
    # Unit B Keys
    b_priv, b_pub = CryptoEngine.generate_x25519_keypair()
    
    # Derive shared secrets
    shared_secret_A = CryptoEngine.derive_symmetric_key(a_priv, b_pub)
    shared_secret_B = CryptoEngine.derive_symmetric_key(b_priv, a_pub)
    
    # Verify both parties generated the exact same AES key
    assert shared_secret_A == shared_secret_B
    
    # Encrypt Payload (Unit A)
    payload = {"mission": "Extract coordinates", "target": "Alpha"}
    nonce, ciphertext = CryptoEngine.encrypt_payload(payload, shared_secret_A)
    
    # Decrypt Payload (Unit B)
    decrypted_payload = CryptoEngine.decrypt_payload(nonce, ciphertext, shared_secret_B)
    assert decrypted_payload["mission"] == "Extract coordinates"

def test_aes_gcm_tamper_detection():
    priv, pub = CryptoEngine.generate_x25519_keypair()
    shared_secret = CryptoEngine.derive_symmetric_key(priv, pub) # Using same key for local test
    
    payload = {"data": "Secure string"}
    nonce, ciphertext = CryptoEngine.encrypt_payload(payload, shared_secret)
    
    # Tamper with ciphertext by modifying the last byte (part of the auth tag)
    tampered_ciphertext = bytearray(ciphertext)
    tampered_ciphertext[-1] ^= 0x01
    
    with pytest.raises(Exception):
        CryptoEngine.decrypt_payload(nonce, bytes(tampered_ciphertext), shared_secret)