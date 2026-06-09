from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget
from PySide6.QtCore import Qt
from ui.views import DashboardView, RequestView, LogsView, UnitManagementView, AssistantView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI BOS - Secure Mission Console")
        self.resize(1100, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #11111b; border-right: 1px solid #313244;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #1e1e2e;")
        
        # Initialize ALL Views
        self.view_dashboard = DashboardView()
        self.view_units = UnitManagementView()       # NEW
        self.view_assistants = AssistantView()       # NEW
        self.view_requests = RequestView()
        self.view_logs = LogsView()

        # Add to stack (Order matters for indexing)
        self.stacked_widget.addWidget(self.view_dashboard)   # 0
        self.stacked_widget.addWidget(self.view_units)       # 1
        self.stacked_widget.addWidget(self.view_assistants)  # 2
        self.stacked_widget.addWidget(self.view_requests)    # 3
        self.stacked_widget.addWidget(self.view_logs)        # 4

        # Navigation Buttons
        self.add_nav_button(sidebar_layout, "📊 Dashboard", 0)
        self.add_nav_button(sidebar_layout, "🤝 Unit Registry", 1)
        self.add_nav_button(sidebar_layout, "🤖 AI Routing Assistants", 2)
        self.add_nav_button(sidebar_layout, "📡 Mission Control", 3)
        self.add_nav_button(sidebar_layout, "🗄️ Secure Logs", 4)
        
        sidebar_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stacked_widget)
        
        # Force refresh UI items on startup
        self.view_units.vm.load_units()
        self.view_assistants.vm.load_assistants()
        self.view_requests.refresh_destinations()

    def add_nav_button(self, layout, text, index):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton { text-align: left; padding: 12px; background-color: transparent; color: #cdd6f4; font-size: 14px; border: none;}
            QPushButton:hover { background-color: #313244; border-radius: 4px; }
        """)
        
        # When changing tabs, refresh lists just in case
        def on_click():
            self.stacked_widget.setCurrentIndex(index)
            if index == 1: self.view_units.vm.load_units()
            if index == 2: self.view_assistants.vm.load_assistants()
            if index == 3: self.view_requests.refresh_destinations()

        btn.clicked.connect(on_click)
        layout.addWidget(btn)

    def closeEvent(self, event):
        event.ignore()
        self.hide()