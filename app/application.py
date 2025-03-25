import sys

from PySide6.QtCore import QCommandLineOption, QCommandLineParser, Qt
from PySide6.QtWidgets import QApplication

from app.apiworker import ApiWorker
from app.mediakeylistener import MediaKeyListener
from app.widgets import MiniPlayerWidget

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

        self._worker = ApiWorker(server=server)
        self._miniplayer = MiniPlayerWidget()

        self._listener = None
        if listen:
            self._listener = MediaKeyListener()
            self._listener.keyPressed.connect(
                self._handle_key_press, Qt.ConnectionType.QueuedConnection
            )
            self._listener.start()

        # Connect mini player signals to worker
        self._miniplayer.playPauseTriggered.connect(self._worker.requestTogglePlayPause)
        self._miniplayer.nextTriggered.connect(self._worker.requestNextTrack)
        self._miniplayer.previousTriggered.connect(self._worker.requestPreviousTrack)
        self._miniplayer.likeTriggered.connect(self._worker.requestToggleLike)
        self._miniplayer.dislikeTriggered.connect(self._worker.requestToggleDislike)

        # Connect worker signals to miniplayer
        self._worker.titleChanged.connect(self._miniplayer.setTitle)
        self._worker.artistChanged.connect(self._miniplayer.setArtist)
        self._worker.playingChanged.connect(self._miniplayer.setPlaying)
        self._worker.likedChanged.connect(self._miniplayer.setLiked)
        self._worker.dislikedChanged.connect(self._miniplayer.setDisliked)
        self._worker.artworkChanged.connect(self._miniplayer.setArtwork)


    def exec(self):
        self._worker.start()
        ret = self._app.exec()
        self._worker.stop()
        if self._listener:
            self._listener.stop()

        return ret

    def _handle_key_press(self, key: Qt.Key):
        if key == Qt.Key.Key_MediaTogglePlayPause:
            self._worker.requestTogglePlayPause()
        elif key == Qt.Key.Key_MediaPlay:
            self._worker.requestPlay()
        elif key == Qt.Key.Key_MediaPause:
            self._worker.requestPause()
        elif key == Qt.Key.Key_MediaNext:
            self._worker.requestNextTrack()
        elif key == Qt.Key.Key_MediaPrevious:
            self._worker.requestPreviousTrack()
