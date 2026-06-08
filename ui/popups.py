from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import QObject, Signal, Slot, Qt

class UIBroker(QObject):
    # Signal now takes (original, clarified, notes, score, response_queue)
    request_approval_signal = Signal(str, str, list, int, object)

    def __init__(self):
        super().__init__()
        self.request_approval_signal.connect(self.show_popup)

    @Slot(str, str, list, int, object)
    def show_popup(self, original, clarified, notes, score, response_queue):
        dialog = QDialog()
        dialog.setWindowTitle("SECURITY ALERT: Human Approval Required")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<b>Security Score:</b> {score}/10"))
        layout.addWidget(QLabel("<b>Original Request:</b>"))
        orig_box = QTextEdit(original); orig_box.setReadOnly(True); layout.addWidget(orig_box)
        layout.addWidget(QLabel("<b>Clarified Request:</b>"))
        clar_box = QTextEdit(clarified); clar_box.setReadOnly(True); layout.addWidget(clar_box)
        
        layout.addWidget(QLabel("<b>Security Notes:</b>"))
        notes_text = "\n".join([f"- {n}" for n in notes])
        notes_box = QTextEdit(notes_text); notes_box.setReadOnly(True); layout.addWidget(notes_box)

        btn_approve = QPushButton("APPROVE")
        btn_approve.setStyleSheet("background-color: green; color: white;")
        btn_reject = QPushButton("REJECT")
        btn_reject.setStyleSheet("background-color: red; color: white;")

        # When clicked, the dialog closes with either Accepted or Rejected state
        btn_approve.clicked.connect(dialog.accept)
        btn_reject.clicked.connect(dialog.reject)

        layout.addWidget(btn_approve)
        layout.addWidget(btn_reject)
        dialog.setLayout(layout)
        
        # Bring to front
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # dialog.exec() blocks the local UI thread and starts a modal event loop.
        # It returns QDialog.Accepted (1) or QDialog.Rejected (0) depending on which button was clicked,
        # or if the user clicked the window's "X" close button (Rejected).
        result_code = dialog.exec()
        
        # Push the final result safely back to the waiting FastAPI thread
        is_approved = (result_code == QDialog.Accepted)
        response_queue.put(is_approved)