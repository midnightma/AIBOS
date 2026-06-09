import sys
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PySide6.QtGui import QIcon, QAction
from ui.main_window import MainWindow

class AIBOSApplication:
    def __init__(self, sys_argv):
        self.app = QApplication(sys_argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray
        
        self.main_window = MainWindow()
        
        self.setup_tray_icon()

    def setup_tray_icon(self):
        # FIX: Use QStyle enum to safely fetch the built-in system icon in PySide6
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        
        self.tray = QSystemTrayIcon(icon, self.app)
        self.tray.setToolTip("AI BOS Security Gateway")
        
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; }")

        action_show = QAction("Open Dashboard", self.app)
        action_show.triggered.connect(self.show_window)
        
        action_quit = QAction("Exit Securely", self.app)
        action_quit.triggered.connect(self.quit_app)

        menu.addAction(action_show)
        menu.addSeparator()
        menu.addAction(action_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        # Trigger opens the window when you click the tray icon
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        self.main_window.show()
        self.main_window.activateWindow()

    def quit_app(self):
        self.tray.hide()
        self.app.quit()

    def run(self):
        # Start minimized to tray (window won't show until user clicks tray)
        return self.app.exec()