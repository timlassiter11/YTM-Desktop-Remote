from webbrowser import get

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app.apiworker import ApiWorker
from app.ui import rc_resources
from app.utils import get_themed_icon, rotate_icon


class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, icon, worker: ApiWorker, parent=None):
        super().__init__(icon, parent)

        self.worker = worker
        self.worker.title_changed.connect(self._update_tooltip)
        self.worker.artist_changed.connect(self._update_tooltip)
        self.worker.play_state_changed.connect(self._update_play_state)
        self.worker.like_state_changed.connect(self._update_like_state)
        self.worker.dislike_state_changed.connect(self._update_dislike_state)
        self.worker.start()

        self.menu = QMenu(parent)
        # Play / Pause
        self.play_pause_action = self.menu.addAction("")
        self.play_pause_action.triggered.connect(self.worker.toggle_play_pause)
        # Next
        self.next_action = self.menu.addAction("Next")
        self.next_action.setIcon(get_themed_icon(":/icons/next.svg"))
        self.next_action.triggered.connect(self.worker.next_track)
        # Previous
        self.prev_action = self.menu.addAction("Previous")
        self.prev_action.setIcon(get_themed_icon(":/icons/prev.svg"))
        self.prev_action.triggered.connect(self.worker.prev_track)

        self.menu.addSeparator()

        self.like_action = self.menu.addAction("Like")
        self.like_action.triggered.connect(self.worker.toggle_like_track)

        self.dislike_action = self.menu.addAction("Dislike")
        self.dislike_action.triggered.connect(self.worker.toggle_dislike_track)

        self.menu.addSeparator()

        # Exit
        self.exit_action = self.menu.addAction("Exit")
        self.exit_action.setIcon(get_themed_icon(":/icons/close.svg"))
        self.exit_action.triggered.connect(QApplication.quit)
        self.setContextMenu(self.menu)

        self.setToolTip("Loading...")
        self._update_play_state()
        self._update_like_state()
        self._update_dislike_state()
        
    @Slot()
    def _update_tooltip(self):
        self.setToolTip(f"{self.worker.title}\n{self.worker.artist}")

    @Slot()
    def _update_play_state(self):
        if self.worker.playing:
            self.play_pause_action.setText("Pause")
            self.play_pause_action.setIcon(get_themed_icon(":/icons/pause.svg"))
        else:
            self.play_pause_action.setText("Play")
            self.play_pause_action.setIcon(get_themed_icon(":/icons/play.svg"))

    @Slot()
    def _update_like_state(self):
        if self.worker.liked:
            icon = get_themed_icon(":/icons/like_fill.svg")
        else:
            icon = get_themed_icon(":/icons/like.svg")
        self.like_action.setIcon(icon)

    @Slot()
    def _update_dislike_state(self):
        if self.worker.disliked:
            icon = get_themed_icon(":/icons/like_fill.svg")
        else:
            icon = get_themed_icon(":/icons/like.svg")
        self.dislike_action.setIcon(rotate_icon(icon, 180))
