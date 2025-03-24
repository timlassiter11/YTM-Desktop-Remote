import qtawesome as qta # type: ignore
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class SystemTrayApp(QSystemTrayIcon):
    triggered = Signal()
    play_pause_triggered = Signal()
    next_triggered = Signal()
    prev_triggered = Signal()
    like_triggered = Signal()
    dislike_triggered = Signal()
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.activated.connect(self._on_activated)

        context_menu = QMenu(parent)
        
        self.play_pause_action = context_menu.addAction("")
        self.play_pause_action.triggered.connect(self.play_pause_triggered)
        
        self.next_action = context_menu.addAction("Next")
        self.next_action.setIcon(qta.icon("mdi.skip-next"))
        self.next_action.triggered.connect(self.next_triggered)
        
        self.prev_action = context_menu.addAction("Previous")
        self.prev_action.setIcon(qta.icon("mdi.skip-previous"))
        self.prev_action.triggered.connect(self.prev_triggered)

        context_menu.addSeparator()

        self.like_action = context_menu.addAction("Like")
        self.like_action.triggered.connect(self.like_triggered)

        self.dislike_action = context_menu.addAction("Dislike")
        self.dislike_action.triggered.connect(self.dislike_triggered)

        context_menu.addSeparator()

        self.exit_action = context_menu.addAction("Exit")
        self.exit_action.setIcon(qta.icon("mdi.close"))
        self.exit_action.triggered.connect(QApplication.quit)

        self.setContextMenu(context_menu)
        self.setPlayState(False)
        self.setLikeState(False)
        self.setDislikeState(False)

    def setPlayState(self, playing: bool):
        if playing:
            self.play_pause_action.setText("Pause")
            self.play_pause_action.setIcon(qta.icon("mdi.pause"))
        else:
            self.play_pause_action.setText("Play")
            self.play_pause_action.setIcon(qta.icon("mdi.play"))

    def setLikeState(self, liked: bool):
        self.like_action.setIcon(
            qta.icon("mdi.thumb-up" if liked else "mdi.thumb-up-outline")
        )

    def setDislikeState(self, disliked: bool):
        self.dislike_action.setIcon(
            qta.icon("mdi.thumb-down" if disliked else "mdi.thumb-down-outline")
        )

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.triggered.emit()
        
