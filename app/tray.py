from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app.ui import rc_resources
from app.utils import get_themed_icon
from app.apiworker import ApiWorker

class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, icon, worker: ApiWorker, parent=None):
        super().__init__(icon, parent)

        self.worker = worker
        self.worker.track_changed.connect(self._update_ui)
        self.worker.artist_changed.connect(self._update_ui)
        self.worker.track_state_changed.connect(self._update_ui)
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
        # Exit
        self.exit_action = self.menu.addAction("Exit")
        self.exit_action.setIcon(get_themed_icon(":/icons/close.svg"))
        self.exit_action.triggered.connect(QApplication.quit)
        self.setContextMenu(self.menu)

    def _update_ui(self):
        self.setToolTip(f"{self.worker.track}\n{self.worker.artist}")
        if self.worker.playing:
            self.play_pause_action.setText("Pause")
            self.play_pause_action.setIcon(get_themed_icon(":/icons/pause.svg"))
        else:
            self.play_pause_action.setText("Play")
            self.play_pause_action.setIcon(get_themed_icon(":/icons/play.svg"))