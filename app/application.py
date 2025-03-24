import sys

from PySide6.QtCore import QCommandLineOption, QCommandLineParser, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.apiworker import ApiWorker
from app.keyboardlistener import MediaKeyListener
from app.ui import rc_resources
from app.widgets import MiniPlayerWidget
from app.widgets.mediaplayertrayicon import MediaPlayerTrayIcon

from . import APP_DESCRIPTION


class Application:
    def __init__(self):
        self._app = QApplication(sys.argv)

        parser = QCommandLineParser()
        parser.setApplicationDescription(APP_DESCRIPTION)
        parser.addHelpOption()
        parser.addVersionOption()

        server_option = QCommandLineOption(
            ["s", "server"],
            "Server URL",
            "server",
            defaultValue="http://localhost:13091",
        )
        parser.addOption(server_option)
        listener_option = QCommandLineOption(["l", "listen"], "Listen for hotkeys")
        parser.addOption(listener_option)
        parser.process(self._app)

        server = parser.value(server_option)
        listen = parser.isSet(listener_option)

        icon = QIcon(":/icons/icon.png")

        self._worker = ApiWorker(server=server)
        self._miniplayer = MiniPlayerWidget()
        self._miniplayer.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self._tray = MediaPlayerTrayIcon(icon)

        self._listener = None
        if listen:
            self._listener = MediaKeyListener()
            self._listener.key_pressed.connect(
                self._handle_key_press, Qt.ConnectionType.QueuedConnection
            )
            self._listener.start()

        # Setup mini player signals
        self._miniplayer.play_pause_triggered.connect(self._worker.toggle_play_pause)
        self._miniplayer.next_triggered.connect(self._worker.next_track)
        self._miniplayer.prev_triggered.connect(self._worker.prev_track)
        self._miniplayer.like_triggered.connect(self._worker.toggle_like_track)
        self._miniplayer.dislike_triggered.connect(self._worker.toggle_dislike_track)
        # Setup tray signals
        self._tray.play_pause_triggered.connect(self._worker.toggle_play_pause)
        self._tray.next_triggered.connect(self._worker.next_track)
        self._tray.prev_triggered.connect(self._worker.prev_track)
        self._tray.like_triggered.connect(self._worker.toggle_like_track)
        self._tray.dislike_triggered.connect(self._worker.toggle_dislike_track)

        # Setup worker signals for mini player
        self._worker.title_changed.connect(self._miniplayer.setTitle)
        self._worker.artist_changed.connect(self._miniplayer.setArtist)
        self._worker.play_state_changed.connect(self._miniplayer.setPlayState)
        self._worker.like_state_changed.connect(self._miniplayer.setLikeState)
        self._worker.dislike_state_changed.connect(self._miniplayer.setDislikeState)
        self._worker.artwork_changed.connect(self._miniplayer.setArtwork)
        # Setup worker signals for tray
        self._worker.play_state_changed.connect(self._tray.setPlayState)
        self._worker.like_state_changed.connect(self._tray.setLikeState)
        self._worker.dislike_state_changed.connect(self._tray.setDislikeState)

        self._tray.triggered.connect(self._tray_triggered)

    def exec(self):
        self._worker.start()
        self._tray.show()
        ret = self._app.exec()
        self._worker.stop()

        if self._listener:
            self._listener.stop()

        return sys.exit(ret)

    def _handle_key_press(self, key: Qt.Key):
        if key == Qt.Key.Key_MediaTogglePlayPause:
            self._worker.toggle_play_pause()
        elif key == Qt.Key.Key_MediaPlay:
            self._worker.play()
        elif key == Qt.Key.Key_MediaPause:
            self._worker.pause()
        elif key == Qt.Key.Key_MediaNext:
            self._worker.next_track()
        elif key == Qt.Key.Key_MediaPrevious:
            self._worker.prev_track()

    def _tray_triggered(self):
        if not self._miniplayer.isVisible():
            pos = self._tray.geometry().topRight()
            size = self._miniplayer.sizeHint()
            self._miniplayer.move(pos.x() - size.width(), pos.y() - size.height())
            self._miniplayer.show()
