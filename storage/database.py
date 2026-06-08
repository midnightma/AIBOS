import sqlite3
import threading
from config import DB_PATH

_local = threading.local()

def get_db_connection() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS units (
        unit_id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL, max_security_level INTEGER DEFAULT 4)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS keys (
        unit_id TEXT PRIMARY KEY, local_priv_ed BLOB, local_pub_ed BLOB, remote_pub_ed BLOB, 
        local_priv_x BLOB, local_pub_x BLOB, remote_pub_x BLOB, FOREIGN KEY(unit_id) REFERENCES units(unit_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
        msg_id TEXT PRIMARY KEY, source_id TEXT, destination_id TEXT, original_request TEXT, 
        clarified_request TEXT, source_score INTEGER, dest_score INTEGER, final_status TEXT, timestamp INTEGER)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS secure_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER, event_type TEXT, 
        encrypted_blob BLOB, prev_hash TEXT, signature BLOB)''')
        
    cursor.execute('''CREATE TABLE IF NOT EXISTS assistants (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL, api_url TEXT NOT NULL)''')
    
    conn.commit()

# --- Assistants Methods ---
def register_assistant(name: str, description: str, api_url: str):
    conn = get_db_connection()
    conn.execute("INSERT INTO assistants (name, description, api_url) VALUES (?, ?, ?)", (name, description, api_url))
    conn.commit()

def get_all_assistants() -> list:
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM assistants").fetchall()
    return [dict(r) for r in rows]

# --- Unit & Key Management Methods ---
def register_unit(unit_id: str, name: str, role: str, max_security: int):
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO units (unit_id, name, role, max_security_level) VALUES (?, ?, ?, ?)", (unit_id, name, role, max_security))
    conn.commit()

def get_unit(unit_id: str) -> dict:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM units WHERE unit_id = ?", (unit_id,)).fetchone()
    return dict(row) if row else None

# NEW: Delete Unit and its Cryptographic Keys
def delete_unit(unit_id: str) -> bool:
    conn = get_db_connection()
    row = conn.execute("SELECT 1 FROM units WHERE unit_id = ?", (unit_id,)).fetchone()
    if not row:
        return False
    # Explicitly delete keys first, then the unit to maintain database integrity
    conn.execute("DELETE FROM keys WHERE unit_id = ?", (unit_id,))
    conn.execute("DELETE FROM units WHERE unit_id = ?", (unit_id,))
    conn.commit()
    return True

def save_keys(unit_id: str, keys_dict: dict):
    conn = get_db_connection()
    conn.execute('''INSERT OR REPLACE INTO keys (unit_id, local_priv_ed, local_pub_ed, remote_pub_ed, local_priv_x, local_pub_x, remote_pub_x)
        VALUES (?, ?, ?, ?, ?, ?, ?)''', (unit_id, keys_dict.get('local_priv_ed'), keys_dict.get('local_pub_ed'), keys_dict.get('remote_pub_ed'), keys_dict.get('local_priv_x'), keys_dict.get('local_pub_x'), keys_dict.get('remote_pub_x')))
    conn.commit()

def get_keys(unit_id: str) -> dict:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM keys WHERE unit_id = ?", (unit_id,)).fetchone()
    return dict(row) if row else None

# --- Auditing & Logging ---
def log_request(msg_id: str, source_id: str, dest_id: str, orig_req: str, clar_req: str, s_score: int, d_score: int, status: str, ts: int):
    conn = get_db_connection()
    conn.execute('''INSERT INTO requests (msg_id, source_id, destination_id, original_request, clarified_request, source_score, dest_score, final_status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (msg_id, source_id, dest_id, orig_req, clar_req, s_score, d_score, status, ts))
    conn.commit()

def request_exists(msg_id: str) -> bool:
    conn = get_db_connection()
    row = conn.execute("SELECT 1 FROM requests WHERE msg_id = ?", (msg_id,)).fetchone()
    return row is not None

init_db()