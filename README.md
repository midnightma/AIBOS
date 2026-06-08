# 🛡️ AI BOS (Artificial Intelligence Based Operations Security)

**Developed by:** Midnight  
**Status:** Production-Ready  

AI BOS is a decentralized, high-security communications gateway designed for transmitting sensitive operational requests between trusted organizational units. It utilizes a **Zero-Trust** architecture, ensuring that every message is evaluated by a strictly local, offline AI, verified cryptographically, and (when necessary) approved by a human operator before processing.

There are no central servers. Every installation acts as its own independent fortress.

## ✨ Key Features
* **🧠 Fully Local AI (No Cloud Leaks):** Powered by `llama.cpp` and Gemma 4. The AI runs 100% locally on CPU. No data is ever sent to OpenAI, Google, or external servers.
* **🔐 Zero-Trust Cryptography:** Uses unique, isolated keypairs for every relationship. Features **X25519** key exchanges, **Ed25519** digital signatures, and **AES-256-GCM** authenticated encryption.
* **🛑 Human-in-the-loop (HITL):** The AI automatically scores the risk of every request (0-10). Routine tasks (0-2) are auto-approved, critical threats (9-10) are auto-rejected, and medium risks (3-8) trigger an asynchronous desktop popup requesting human approval.
* **🤖 Autonomous AI Routing:** Destination units can define external "Assistants" (APIs). The receiving AI automatically selects the correct assistant, executes the task, and returns an encrypted result payload.
* **📡 Air-Gap Ready:** Operates seamlessly via network APIs or by generating encrypted `.aibos` files that can be securely transferred via USB between offline systems.

---

## ⚙️ How It Works (The Workflow)

1. **The Request:** An operator sends a natural language API request to their local Source Unit.
2. **Source AI Check:** The local AI evaluates the request against organizational policies, scores the risk, and asks for manual GUI approval if necessary.
3. **Cryptographic Packaging:** The request is signed and encrypted into an `.aibos` payload exclusively for the Destination Unit.
4. **Destination Check:** The receiving node decrypts the payload, verifies the digital signature, and runs *its own* independent AI check. 
5. **Execution:** If approved, the Destination AI routes the prompt to an integrated Assistant (like a database query or image generator), captures the result, and encrypts it back to the Source.

---

## 🚀 Getting Started (Development Setup)

### 1. Prerequisites
* Python 3.12+
* An OS with a graphical desktop environment (for PySide6 security popups)
* Download the AI Model: You **must** download `gemma-4-e4b-q4_k_m.gguf` (or your preferred local model) and place it in the `models/` directory.

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/yourusername/aibos.git
cd aibos
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python main.py
```
The server will silently start listening on `https://0.0.0.0:8443`. **Note: The application is headless by design.** A GUI window will only appear when an AI risk assessment requires your manual approval.

---

## 📡 API Reference

AI BOS is entirely controlled via REST APIs. 

### Identity & Information
* `GET /info` - Returns your node's permanent Cryptographic UUID.

### Trust Management (Key Exchange)
* `POST /trusted-source` - Register an external unit authorized to send missions to you. Returns your unique public keys for them.
* `POST /trusted-destination` - Register an external unit you want to send missions to.
* `GET /sources` - List all trusted incoming units.
* `GET /destinations` - List all trusted outgoing units.
* `DELETE /trusted-source/{id}` - Permanently revoke trust and delete keys for a source.
* `DELETE /trusted-destination/{id}` - Permanently revoke trust and delete keys for a destination.

### Assistants & Routing
* `POST /assistant` - Register an execution API for your local node. *(e.g., `{"name": "Search", "description": "...", "api_url": "https://api.com/?q={TEXT}"}`)*

### Mission Execution
* `POST /request` - Submit a natural language mission destined for a trusted unit. Generates an outgoing `.aibos` file.
* `POST /incoming` - Ingest and process an encrypted `.aibos` payload received from a trusted source.
* `POST /response` - Ingest the encrypted results returned from a completed mission.

---

## 📦 Building for Production (Executables)

You can compile AI BOS into a completely self-contained, single-folder executable. The end-user will not need to install Python or any dependencies.

### Linux Build
1. Ensure you are in your virtual environment.
2. Run PyInstaller using the included specification file:
   ```bash
   pyinstaller build.spec
   ```
3. Copy your `.gguf` AI model into the newly generated `dist/AI_BOS/models/` folder.
4. Run the application natively:
   ```bash
   cd dist/AI_BOS/
   ./AI_BOS
   ```

### Windows Build (.exe)
*Note: To create a Windows executable, you **must** run PyInstaller on a Windows machine.*
1. Install Python, activate your virtual environment, and install `requirements.txt`.
2. Run PyInstaller:
   ```cmd
   pyinstaller build.spec
   ```
3. Copy your `.gguf` AI model into `dist\AI_BOS\models\`.
4. **(Optional)** Use the included `installer.iss` script with **Inno Setup** to package the `dist/AI_BOS/` folder into a professional `AIBOS_Setup.exe` Windows installer.

---

## 🛡️ Security Notes
* **Policies:** You can alter the AI's behavior and risk tolerance by modifying the `policies/security_policy.md` text file. 
* **Logs:** Every action, AI decision, and cryptographic failure is permanently written to `data/aibos.db` in a tamper-evident, cryptographically chained ledger.
* **Local Identity:** Your node's UUID is automatically generated on the first run and stored in `data/node_id.txt`. Keep your `data/aibos.db` secure, as it holds your private ECDH and EdDSA keys.

---
**Architected and engineered by Midnight.**  
*Security Above Everything Else.*