import sys
import threading
import os
from fastapi import FastAPI
import uvicorn
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config import CERTS_DIR
from ui.popups import UIBroker
from core.workflow import AIBOSWorkflow
from api.routes import router
import api.routes

app = FastAPI(title="AI BOS API", description="Secure Mission Transfer Node")

# Include the API router
app.include_router(router)

def generate_self_signed_cert(cert_path: str, key_path: str):
    """Generates a self-signed TLS certificate if none exists for secure Uvicorn execution."""
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    import datetime

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

def run_api():
    """Runs the FastAPI application using Uvicorn with TLS enabled."""
    cert_file = os.path.join(CERTS_DIR, "cert.pem")
    key_file = os.path.join(CERTS_DIR, "key.pem")
    
    generate_self_signed_cert(cert_file, key_file)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8443, 
        ssl_keyfile=key_file, 
        ssl_certfile=cert_file,
        log_level="warning"
    )

if __name__ == "__main__":
    # 1. Initialize the Qt Application (Must be in the main thread)
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False) # Keep running in the background

    # 2. Initialize UI Broker for asynchronous cross-thread signaling
    ui_broker = UIBroker()

    # 3. Initialize the core workflow and inject it into the API router
    print("Loading AI Model and verifying database. This may take a moment...")
    workflow_instance = AIBOSWorkflow(ui_broker=ui_broker)
    api.routes.workflow_instance = workflow_instance

    # 4. Start the FastAPI server in a background daemon thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    print("AI BOS System Initialized. Listening on port 8443 (HTTPS).")

    # 5. Start the Qt Event Loop
    sys.exit(qt_app.exec())