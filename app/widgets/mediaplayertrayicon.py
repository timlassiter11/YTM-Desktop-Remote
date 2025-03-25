import qtawesome as qta # type: ignore
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class MediaPlayerTrayIcon(QSystemTrayIcon):
    triggered = Signal()
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.activated.connect(self._on_activated)

        context_menu = QMenu(parent)
        self.exit_action = context_menu.addAction("Exit")
        self.exit_action.setIcon(qta.icon("mdi.close"))
        self.exit_action.triggered.connect(QApplication.quit)

        self.setContextMenu(context_menu)

        self.installEventFilter(self)
    
    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.triggered.emit()
        
