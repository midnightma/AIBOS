# 🛡️ AI BOS (Artificial Intelligence Based Operations Security)

**Developed by:** [Midnight](https://github.com/MidnightMA)  
**Status:** Production-Ready  

**AI BOS** is a decentralized, zero-trust communications gateway designed to securely transmit, evaluate, and execute sensitive operational requests between isolated organizational units. 

Instead of relying on a centralized server, every AI BOS node is an independent fortress. The system ensures that no request is sent, received, or executed without passing three strict layers of verification: **Local AI risk evaluation**, **Cryptographic validation**, and **Manual operator approval (Human-in-the-Loop)**.

## ✨ Key Features

*   **🧠 100% Local AI (Air-Gap Ready):** Powered by `llama.cpp` and local GGUF models (e.g., Gemma 4). The AI evaluates policies and routes tasks directly on your CPU. No cloud APIs, no data leaks.
*   **🔐 Zero-Trust Cryptography:** 
    *   Unique **X25519** ECDH key exchanges per relationship.
    *   **Ed25519** digital signatures prevent spoofing and repudiation.
    *   **AES-256-GCM** authenticated encryption protects payload integrity.
*   **🛑 Human-in-the-loop (HITL):** The AI scores the risk of every natural language request (0-10). Routine tasks (0-2) are auto-approved, critical threats (9-10) are auto-rejected, and medium risks (3-8) trigger an un-bypassable GUI prompt requesting human authorization.
*   **🤖 Active AI Routing (Assistants):** Destination units can register local API endpoints (e.g., Image Generation, Database Queries). The Destination AI automatically selects the correct assistant, injects the authorized prompt, executes the task, and securely encrypts the result back to the Source.
*   **🖥️ Desktop Management Console:** A fully cross-platform (Windows & Linux) PySide6 desktop interface for managing keys, viewing tamper-evident logs, and processing offline `.aibos` mission files.

---

## ⚙️ The Mission Lifecycle

1.  **Request Generation:** An operator types a natural language request in the UI.
2.  **Source AI Check:** The local AI translates the request, scores the risk, and asks the local operator for approval.
3.  **Cryptographic Packaging:** The request is signed and encrypted into an `.aibos` payload exclusively for the Destination Unit's public keys.
4.  **Destination Verification:** The receiving node decrypts the payload, verifies the digital signature to ensure identity, and runs *its own* independent AI risk assessment.
5.  **Execution & Response:** Once approved by the Destination operator, the Destination AI routes the prompt to an integrated Assistant, captures the result, encrypts it, and returns a response `.aibos` package.
6.  **Results Review:** The Source Unit decrypts the response package and views the results securely on their dashboard.

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.12+
*   An OS with a graphical desktop environment.
*   **AI Model:** Download a local GGUF model (e.g., `gemma-4-e4b-q4_k_m.gguf`) and place it inside the `models/` directory.

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/MidnightMA/AIBOS.git
cd AIBOS
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```
The application will launch the **Desktop Management Console**, drop a secure icon into your system tray, and start the background API server silently on `https://0.0.0.0:8443`.

---

## 🖥️ Desktop UI Guide

The PySide6 interface is designed as an isolated administrative overlay. To prevent privilege escalation and network attack vectors, **the UI does not use localhost REST APIs**; it connects directly to the core Python business logic.

*   **📊 Dashboard:** View your node's cryptographic UUID, trust configurations, and active logs.
*   **🤝 Unit Registry:** Perform secure cryptographic handshakes. Register Source and Destination units, and manage public X25519/Ed25519 keys.
*   **🤖 AI Routing Assistants:** Define external local helpers. Input an API URL containing `{TEXT}`. The AI will automatically replace `{TEXT}` with optimized prompts during task execution.
*   **📡 Mission Control:** Draft outbound requests, or import inbound `.aibos` encrypted files to execute missions and decrypt responses.
*   **🗄️ Secure Logs:** View the strictly read-only SQLite ledger. Every action is cryptographically chained with previous-hash tracking for tamper evidence.

---

## 📡 Headless REST API Reference

For system-to-system integrations, AIBOS exposes a secure REST API backend.

*   `GET /info` - Returns your node's permanent UUID.
*   `GET /sources` & `GET /destinations` - List trusted network units.
*   `POST /trusted-source` & `POST /trusted-destination` - Exchange public keys and establish mutual Zero-Trust relationships.
*   `POST /assistant` - Register a local execution assistant.
*   `POST /request` - Submit an outbound mission. Triggers local AI, HITL, and returns an `.aibos` file.
*   `POST /incoming` - Ingest an inbound `.aibos` package. Triggers destination AI, execution, and returns a response package.
*   `POST /response` - Decrypt and view an inbound mission response package.

---

## 📦 Building for Production

AI BOS can be packaged into a standalone executable (no Python installation required for end-users). 

### Linux Build
```bash
# Clear previous builds
rm -rf build/ dist/
# Compile application
pyinstaller build.spec
# Copy your AI model into the fresh build directory
cp models/gemma-4-e4b-q4_k_m.gguf dist/AI_BOS/models/
# Run natively
./dist/AI_BOS/AI_BOS
```

### Windows Build (.exe)
*Note: PyInstaller is not a cross-compiler. You must run this on a Windows machine or VM.*
```cmd
pyinstaller build.spec
copy models\gemma-4-e4b-q4_k_m.gguf dist\AI_BOS\models\
```
*(Optional: Use the included `installer.iss` with Inno Setup to create a professional `AIBOS_Setup.exe` installer).*

---

## 🛡️ Security Principles

*   **No Central Authority:** Units share keys peer-to-peer. The compromise of one relationship does not breach the network.
*   **No API Loopback:** The UI and Core run in unified memory. Desktop operations cannot be intercepted via localhost SSRF.
*   **Deterministic Policies:** Security thresholds and definitions are stored in plain text at `policies/security_policy.md` and injected transparently into the AI context window.
*   **Anti-Replay Architecture:** Every `.aibos` payload includes AES-GCM nonces, epoch timestamps, and UUIDs to permanently block intercepted packet replay attacks.

---
**Architected and engineered by Midnight.**  
*Security Above Everything Else.*