import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QTextEdit, 
    QMessageBox, QHeaderView, QComboBox, QFileDialog, QGroupBox, QSpinBox
)
from PySide6.QtCore import Qt, QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices
from ui.viewmodels import DashboardViewModel, UnitManagementViewModel, LogsViewModel, AssistantViewModel
from ui.workers import AsyncCoreWorker
from storage.database import get_db_connection

class BaseView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', Arial; }
            QLabel { font-size: 14px; }
            QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #b4befe; }
            QTableWidget { background-color: #181825; alternate-background-color: #1e1e2e; border: 1px solid #313244; }
            QHeaderView::section { background-color: #313244; padding: 4px; border: none; font-weight: bold; }
            QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #11111b; border: 1px solid #45475a; padding: 5px; color: #cdd6f4; }
            QGroupBox { font-weight: bold; border: 1px solid #45475a; border-radius: 5px; margin-top: 1ex; padding: 10px;}
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }
        """)

class DashboardView(BaseView):
    def __init__(self):
        super().__init__()
        self.vm = DashboardViewModel()
        self.vm.data_updated.connect(self.update_ui)
        layout = QVBoxLayout(self)
        
        title = QLabel("🛡️ AIBOS Management Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #a6e3a1;")
        layout.addWidget(title)
        self.info_label = QLabel("Loading data securely...")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        btn_refresh = QPushButton("Refresh Status")
        btn_refresh.clicked.connect(self.vm.refresh_data)
        layout.addWidget(btn_refresh)
        layout.addStretch()
        self.vm.refresh_data()

    def update_ui(self, data: dict):
        self.info_label.setText(
            f"<b>Local Node ID (UUID):</b> {data['local_node_id']}<br><br>"
            f"<b>Trusted Sources:</b> {data['sources_count']}<br>"
            f"<b>Trusted Destinations:</b> {data['destinations_count']}<br>"
            f"<b>Pending Approvals:</b> {data['pending_approvals']}<br>"
            f"<b>Cryptographic Log Entries:</b> {data['total_logs']}<br>"
        )

# NEW: Unit Management View
class UnitManagementView(BaseView):
    def __init__(self):
        super().__init__()
        self.vm = UnitManagementViewModel()
        self.vm.units_loaded.connect(self.populate_table)
        self.vm.operation_result.connect(self.on_operation_result)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Network Units Directory</b>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Unit ID", "Name", "Role", "Max Risk Level"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        btn_delete = QPushButton("Delete Selected Unit")
        btn_delete.setStyleSheet("background-color: #f38ba8;")
        btn_delete.clicked.connect(self.delete_selected)
        layout.addWidget(btn_delete)

        # Registration Form
        form_group = QGroupBox("Register New Trusted Unit")
        form_layout = QVBoxLayout()
        
        self.inp_id = QLineEdit(); self.inp_id.setPlaceholderText("Remote Unit UUID")
        self.inp_name = QLineEdit(); self.inp_name.setPlaceholderText("Display Name")
        self.inp_role = QComboBox(); self.inp_role.addItems(["SOURCE", "DESTINATION"])
        self.inp_risk = QSpinBox(); self.inp_risk.setRange(1, 10); self.inp_risk.setValue(4)
        self.inp_pub_ed = QLineEdit(); self.inp_pub_ed.setPlaceholderText("Remote Ed25519 Public Key (Leave blank for initial setup)")
        self.inp_pub_x = QLineEdit(); self.inp_pub_x.setPlaceholderText("Remote X25519 Public Key (Leave blank for initial setup)")
        
        form_layout.addWidget(self.inp_id); form_layout.addWidget(self.inp_name)
        form_layout.addWidget(QLabel("Role & Max Permitted Security Level:")); 
        form_layout.addWidget(self.inp_role); form_layout.addWidget(self.inp_risk)
        form_layout.addWidget(self.inp_pub_ed); form_layout.addWidget(self.inp_pub_x)
        
        btn_add = QPushButton("Register & Generate Local Keys")
        btn_add.clicked.connect(self.register_unit)
        form_layout.addWidget(btn_add)
        form_group.setLayout(form_layout)
        
        layout.addWidget(form_group)
        self.vm.load_units()

    def register_unit(self):
        self.vm.add_unit(self.inp_id.text().strip(), self.inp_name.text().strip(), self.inp_role.currentText(),
                         self.inp_risk.value(), self.inp_pub_ed.text().strip(), self.inp_pub_x.text().strip())

    def delete_selected(self):
        row = self.table.currentRow()
        if row < 0: return
        unit_id = self.table.item(row, 0).text()
        self.vm.delete_unit_entry(unit_id)

    def populate_table(self, units: list):
        self.table.setRowCount(len(units))
        for r, u in enumerate(units):
            self.table.setItem(r, 0, QTableWidgetItem(u['unit_id']))
            self.table.setItem(r, 1, QTableWidgetItem(u['name']))
            self.table.setItem(r, 2, QTableWidgetItem(u['role']))
            self.table.setItem(r, 3, QTableWidgetItem(str(u['max_security_level'])))

    def on_operation_result(self, success, msg):
        if success:
            QMessageBox.information(self, "Success", msg)
            self.vm.load_units()
        else:
            QMessageBox.critical(self, "Error", msg)

# NEW: Assistant Management View
class AssistantView(BaseView):
    def __init__(self):
        super().__init__()
        self.vm = AssistantViewModel()
        self.vm.assistants_loaded.connect(self.populate_table)
        self.vm.operation_result.connect(self.on_operation_result)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>AI Routing Assistants Directory</b>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Description", "API URL"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        form_group = QGroupBox("Register New Assistant")
        form_layout = QVBoxLayout()
        self.inp_name = QLineEdit(); self.inp_name.setPlaceholderText("Assistant Name")
        self.inp_desc = QLineEdit(); self.inp_desc.setPlaceholderText("Description for AI Selection logic")
        self.inp_url = QLineEdit(); self.inp_url.setPlaceholderText("API URL (Must contain {TEXT})")
        
        form_layout.addWidget(self.inp_name); form_layout.addWidget(self.inp_desc); form_layout.addWidget(self.inp_url)
        btn_add = QPushButton("Register Assistant")
        btn_add.clicked.connect(self.add_assistant)
        form_layout.addWidget(btn_add)
        form_group.setLayout(form_layout)
        
        layout.addWidget(form_group)
        self.vm.load_assistants()

    def add_assistant(self):
        self.vm.add_assistant(self.inp_name.text().strip(), self.inp_desc.text().strip(), self.inp_url.text().strip())

    def populate_table(self, assistants: list):
        self.table.setRowCount(len(assistants))
        for r, a in enumerate(assistants):
            self.table.setItem(r, 0, QTableWidgetItem(a['name']))
            self.table.setItem(r, 1, QTableWidgetItem(a['description']))
            self.table.setItem(r, 2, QTableWidgetItem(a['api_url']))

    def on_operation_result(self, success, msg):
        QMessageBox.information(self, "Result", msg) if success else QMessageBox.critical(self, "Error", msg)
        if success: self.vm.load_assistants()

# MODIFIED: RequestView to support importing Responses
class RequestView(BaseView):
    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("<b>Create Secure Mission Request</b>"))
        self.dest_combo = QComboBox()
        self.refresh_destinations()
        layout.addWidget(QLabel("Target Destination:"))
        layout.addWidget(self.dest_combo)
        layout.addWidget(QLabel("Natural Language Request:"))
        self.text_input = QTextEdit()
        layout.addWidget(self.text_input)

        self.btn_send = QPushButton("Encrypt & Process Mission")
        self.btn_send.clicked.connect(self.process_request)
        layout.addWidget(self.btn_send)
        
        # Split Import Section
        layout.addWidget(QLabel("<hr><b>Offline Inbound Payloads</b>"))
        btn_layout = QHBoxLayout()
        
        self.btn_import_req = QPushButton("📥 Import Incoming Mission (Execute)")
        self.btn_import_req.setStyleSheet("background-color: #fab387; color: #11111b;")
        self.btn_import_req.clicked.connect(lambda: self.import_file("incoming"))
        
        self.btn_import_res = QPushButton("📬 Import Mission Response (View Result)")
        self.btn_import_res.setStyleSheet("background-color: #a6e3a1; color: #11111b;")
        self.btn_import_res.clicked.connect(lambda: self.import_file("response"))
        
        btn_layout.addWidget(self.btn_import_req)
        btn_layout.addWidget(self.btn_import_res)
        layout.addLayout(btn_layout)

    def refresh_destinations(self):
        self.dest_combo.clear()
        conn = get_db_connection()
        dests = conn.execute("SELECT unit_id, name FROM units WHERE role='DESTINATION'").fetchall()
        for d in dests: self.dest_combo.addItem(f"{d['name']} ({d['unit_id']})", d['unit_id'])

    def process_request(self):
        if self.dest_combo.currentIndex() == -1: return
        dest_id = self.dest_combo.currentData()
        req_text = self.text_input.toPlainText().strip()
        if not req_text: return
        self.btn_send.setEnabled(False)
        self.btn_send.setText("Processing via Local AI...")

        worker = AsyncCoreWorker(action="process_outgoing", destination_id=dest_id, request_text=req_text)
        worker.signals.finished.connect(self.on_process_success)
        worker.signals.error.connect(self.on_process_error)
        self.thread_pool.start(worker)

    def on_process_success(self, result: dict):
        self.btn_send.setEnabled(True); self.btn_send.setText("Encrypt & Process Mission")
        QMessageBox.information(self, "Mission Approved", f"Mission processed.\nPackage path: {result.get('package_path')}")

    def on_process_error(self, err: str):
        self.btn_send.setEnabled(True); self.btn_send.setText("Encrypt & Process Mission")
        QMessageBox.critical(self, "Rejected", f"Execution blocked:\n{err}")

    def import_file(self, action_type: str):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open AIBOS Package", "", "AIBOS Files (*.aibos)")
        if not file_name: return
        try:
            with open(file_name, 'r') as f: package_data = json.load(f)
            # Route to correct worker action
            action_code = "process_incoming" if action_type == "incoming" else "process_response"
            worker = AsyncCoreWorker(action=action_code, package_data=package_data)
            
            # Setup custom success callback depending on the type of import
            if action_type == "incoming":
                worker.signals.finished.connect(lambda res: QMessageBox.information(self, "Mission Execution", str(res)))
            else:
                worker.signals.finished.connect(self.on_response_success)
                
            worker.signals.error.connect(lambda err: QMessageBox.critical(self, "Security Violation", f"Payload rejected:\n{err}"))
            self.thread_pool.start(worker)
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to read file: {str(e)}")

    def on_response_success(self, result: dict):
        # Open the folder where the extracted file was saved natively
        fp = result.get('file_path')
        QMessageBox.information(self, "Response Decrypted", f"Assistant Used: {result.get('assistant_used')}\nSaved to:\n{fp}")
        if fp and os.path.exists(fp):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(fp)))

class LogsView(BaseView):
    def __init__(self):
        super().__init__()
        self.vm = LogsViewModel()
        self.vm.logs_loaded.connect(self.populate_table)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Cryptographic Tamper-Evident Ledger</b>"))
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Event Type", "Previous Hash"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        btn_refresh = QPushButton("Pull Secure Logs")
        btn_refresh.clicked.connect(lambda: self.vm.load_logs(100))
        layout.addWidget(btn_refresh)
        self.vm.load_logs(100)

    def populate_table(self, logs: list):
        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            import datetime
            dt = datetime.datetime.fromtimestamp(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            self.table.setItem(row, 0, QTableWidgetItem(dt))
            self.table.setItem(row, 1, QTableWidgetItem(log['event_type']))
            self.table.setItem(row, 2, QTableWidgetItem(log['prev_hash'][:16] + "..."))