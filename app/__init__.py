import json
import locale
import sys

# If we don't import QtSvg,
# the get_themed_icon function doesn't work.
from PySide6 import QtSvg
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QRestAccessManager,
    QRestReply,
)
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from pynput import keyboard

from app.ui import rc_resources

VERSION = "1.0.0"
APP_NAME = "YTM Desktop Remote"
APP_DESCRIPTION = "Remote control for Youtube Music Desktop Application"
APP_AUTHOR = "Timothy Lassiter"
DOMAIN_NAME = ""
ORGANIZATION_NAME = ""


class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, icon, server="http://localhost:13091", parent=None):
        super().__init__(icon, parent)
        self._server = server
        self._state_changing = False
        if self._server.endswith("/"):
            self._server = self._server[:-1]

        self.menu = QMenu(parent)
        # Play / Pause
        self.play_pause_action = self.menu.addAction("")
        self.play_pause_action.triggered.connect(self.toggle_play_pause)
        # Previous
        self.prev_action = self.menu.addAction("Previous")
        self.prev_action.setIcon(get_themed_icon(":/icons/prev.svg"))
        self.prev_action.triggered.connect(self.prev_track)
        # Next
        self.next_action = self.menu.addAction("Next")
        self.next_action.setIcon(get_themed_icon(":/icons/next.svg"))
        self.next_action.triggered.connect(self.next_track)

        self.menu.addSeparator()
        # Exit
        self.exit_action = self.menu.addAction("Exit")
        self.exit_action.setIcon(get_themed_icon(":/icons/close.svg"))
        self.exit_action.triggered.connect(QApplication.quit)
        self.setContextMenu(self.menu)

        self._playing = True
        self.playing = False

        self._network_manager = QRestAccessManager(QNetworkAccessManager(self))
        self._timer = QTimer(self, singleShot=True)
        self._timer.timeout.connect(self._update_status)
        self._update_status()

    @property
    def playing(self) -> bool:
        return self._playing

    @playing.setter
    def playing(self, value: bool):
        if self._playing == value:
            return

        self._playing = value
        if value is True:
            self.play_pause_action.setText("Pause")
            self.play_pause_action.setIcon(get_themed_icon(":/icons/pause.svg"))
        else:
            self.play_pause_action.setText("Play")
            self.play_pause_action.setIcon(get_themed_icon(":/icons/play.svg"))

    def _update_status(self):
        self._timer.stop()
        req = QNetworkRequest(f"{self._server}/track")
        self._network_manager.get(req, self, self._handle_track_reply)
        req = QNetworkRequest(f"{self._server}/track/state")
        self._network_manager.get(req, self, self._handle_state_reply)

    def _handle_track_reply(self, reply: QRestReply):
        if reply.isSuccess():
            data = json.loads(reply.readText())
            title = data["video"]["title"]
            artist = data["video"]["author"]
            self.setToolTip(f"{title}\n{artist}")

        self._timer.start(1000)

    def _handle_state_reply(self, reply: QRestReply):
        if not self._state_changing and reply.isSuccess():
            data = json.loads(reply.readText())
            self.playing = data["playing"]

    def _handle_play_pause_reply(self, reply: QRestReply):
        if reply.isSuccess():
            data = json.loads(reply.readText())
            self.playing = data["isPlaying"]
        self._state_changing = False

    def prev_track(self):
        req = QNetworkRequest(f"{self._server}/track/prev")
        self._network_manager.post(req, {}, self, lambda reply: self._update_status())

    def next_track(self):
        req = QNetworkRequest(f"{self._server}/track/next")
        self._network_manager.post(req, {}, self, lambda reply: self._update_status())

    def toggle_play_pause(self):
        if self.playing:
            url = f"{self._server}/track/pause"
        else:
            url = f"{self._server}/track/play"

        self.playing = not self.playing
        self._state_changing = True

        req = QNetworkRequest(url)
        self._network_manager.post(req, {}, self, self._handle_play_pause_reply)

    def play(self):
        if not self.playing:
            self.toggle_play_pause()
        

    def pause(self):
        if self.playing:
            self.toggle_play_pause()


def run():
    locale.setlocale(locale.LC_ALL, "")

    QApplication.setOrganizationName(ORGANIZATION_NAME)
    QApplication.setOrganizationDomain(DOMAIN_NAME)
    QApplication.setApplicationName(APP_NAME)
    QApplication.setApplicationVersion(VERSION)

    app = QApplication(sys.argv)

    try:
        index = sys.argv.index("server")
        server = sys.argv[index + 1]
    except ValueError:
        server = "http://localhost:13091"

    icon = QIcon(":/icons/icon.png")
    tray = SystemTrayApp(icon, server=server)
    tray.show()

    def on_press(key):
        if key == keyboard.Key.media_play_pause:
            print("Play/pause key pressed")
        elif key == keyboard.Key.media_next:
            print("Next track key pressed")
        elif key == keyboard.Key.media_previous:
            print("Previous track key pressed")

    listener_thread = keyboard.Listener(on_press=on_press)
    listener_thread.start()

    ret = app.exec()
    listener_thread.stop()
    listener_thread.join()
    return ret


def get_themed_icon(svg_filepath, color: QColor | None = None) -> QIcon:
    if color is None:
        color = QApplication.palette().color(QPalette.ColorRole.WindowText)

    img = QPixmap(svg_filepath)
    qp = QPainter(img)
    qp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    qp.fillRect(img.rect(), color)
    qp.end()
    return QIcon(img)
