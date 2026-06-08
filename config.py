import os
import sys
import uuid
import shutil

# Determine execution context (Source code vs PyInstaller compiled)
if getattr(sys, 'frozen', False):
    # We are running as a PyInstaller bundle.
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLED_DIR = sys._MEIPASS
else:
    # We are running from Python source
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLED_DIR = BASE_DIR

# Define user-facing directories OUTSIDE of _internal
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
POLICIES_DIR = os.path.join(BASE_DIR, "policies")
TRANSFERS_DIR = os.path.join(BASE_DIR, "transfers")
IMPORT_DIR = os.path.join(BASE_DIR, "import")
CERTS_DIR = os.path.join(BASE_DIR, "certs")

# Ensure directories exist
for directory in [DATA_DIR, MODELS_DIR, POLICIES_DIR, TRANSFERS_DIR, IMPORT_DIR, CERTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Specific File Paths
DB_PATH = os.path.join(DATA_DIR, "aibos.db")
POLICY_PATH = os.path.join(POLICIES_DIR, "security_policy.md")

# --- AUTO-EXTRACT POLICY ---
internal_policy = os.path.join(BUNDLED_DIR, "policies", "security_policy.md")
if not os.path.exists(POLICY_PATH) and os.path.exists(internal_policy):
    shutil.copy(internal_policy, POLICY_PATH)

# --- SMART MODEL DETECTION ---
external_model = os.path.join(MODELS_DIR, "gemma-4-e4b-q4_k_m.gguf")
internal_model = os.path.join(BUNDLED_DIR, "models", "gemma-4-e4b-q4_k_m.gguf")

# If the user explicitly placed a model in the external folder, use that one.
# Otherwise, seamlessly read the one already packed inside _internal!
if os.path.exists(external_model):
    MODEL_PATH = external_model
elif os.path.exists(internal_model):
    MODEL_PATH = internal_model
else:
    MODEL_PATH = external_model  # Fallback so the error points to the user folder

# Generate a local node ID if it doesn't exist
NODE_ID_FILE = os.path.join(DATA_DIR, "node_id.txt")
if not os.path.exists(NODE_ID_FILE):
    with open(NODE_ID_FILE, "w") as f:
        f.write(str(uuid.uuid4()))

with open(NODE_ID_FILE, "r") as f:
    LOCAL_NODE_ID = f.read().strip()