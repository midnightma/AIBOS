from PySide6.QtCore import QObject, Signal
import base64
from storage.database import get_db_connection, delete_unit, register_unit, save_keys, register_assistant, get_all_assistants
from security.crypto_engine import CryptoEngine
from cryptography.hazmat.primitives import serialization
from config import LOCAL_NODE_ID

class DashboardViewModel(QObject):
    data_updated = Signal(dict)

    def refresh_data(self):
        conn = get_db_connection()
        sources = conn.execute("SELECT COUNT(*) FROM units WHERE role='SOURCE'").fetchone()[0]
        dests = conn.execute("SELECT COUNT(*) FROM units WHERE role='DESTINATION'").fetchone()[0]
        logs = conn.execute("SELECT COUNT(*) FROM secure_logs").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM requests WHERE final_status='PENDING'").fetchone()[0]
        
        self.data_updated.emit({
            "local_node_id": LOCAL_NODE_ID,
            "sources_count": sources,
            "destinations_count": dests,
            "total_logs": logs,
            "pending_approvals": pending
        })

class UnitManagementViewModel(QObject):
    units_loaded = Signal(list)
    operation_result = Signal(bool, str)

    def load_units(self):
        conn = get_db_connection()
        rows = conn.execute("SELECT unit_id, name, role, max_security_level FROM units").fetchall()
        self.units_loaded.emit([dict(r) for r in rows])

    def add_unit(self, unit_id: str, name: str, role: str, max_security: int, remote_pub_ed_b64: str, remote_pub_x_b64: str):
        try:
            priv_ed, pub_ed = CryptoEngine.generate_ed25519_keypair()
            priv_x, pub_x = CryptoEngine.generate_x25519_keypair()
            
            priv_ed_bytes = priv_ed.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
            pub_ed_bytes = pub_ed.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
            priv_x_bytes = priv_x.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
            pub_x_bytes = pub_x.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)

            register_unit(unit_id, name, role, max_security)
            save_keys(unit_id, {
                "local_priv_ed": priv_ed_bytes, "local_pub_ed": pub_ed_bytes,
                "remote_pub_ed": base64.b64decode(remote_pub_ed_b64),
                "local_priv_x": priv_x_bytes, "local_pub_x": pub_x_bytes,
                "remote_pub_x": base64.b64decode(remote_pub_x_b64)
            })
            
            local_pub_ed_str = base64.b64encode(pub_ed_bytes).decode('utf-8')
            local_pub_x_str = base64.b64encode(pub_x_bytes).decode('utf-8')
            
            msg = f"Unit registered successfully.\n\nYour Pub Ed Key: {local_pub_ed_str}\nYour Pub X Key: {local_pub_x_str}"
            self.operation_result.emit(True, msg)
        except Exception as e:
            self.operation_result.emit(False, f"Registration failed: {str(e)}")

    def delete_unit_entry(self, unit_id: str):
        if delete_unit(unit_id):
            self.operation_result.emit(True, f"Unit {unit_id} permanently deleted.")
        else:
            self.operation_result.emit(False, "Failed to delete unit.")

class AssistantViewModel(QObject):
    assistants_loaded = Signal(list)
    operation_result = Signal(bool, str)
    
    def load_assistants(self):
        assistants = get_all_assistants()
        self.assistants_loaded.emit(assistants)
        
    def add_assistant(self, name: str, description: str, api_url: str):
        try:
            register_assistant(name, description, api_url)
            self.operation_result.emit(True, f"Assistant '{name}' registered successfully.")
        except Exception as e:
            self.operation_result.emit(False, f"Failed to register assistant: {str(e)}")

class LogsViewModel(QObject):
    logs_loaded = Signal(list)

    def load_logs(self, limit=100):
        conn = get_db_connection()
        rows = conn.execute("SELECT timestamp, event_type, prev_hash FROM secure_logs ORDER BY log_id DESC LIMIT ?", (limit,)).fetchall()
        self.logs_loaded.emit([dict(r) for r in rows])