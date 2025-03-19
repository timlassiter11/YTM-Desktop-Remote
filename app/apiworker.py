import json
import logging
import typing

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
    QRestAccessManager,
    QRestReply,
)

_logger = logging.getLogger(__name__)


class ApiWorker(QObject):
    track_changed = Signal(str)
    artist_changed = Signal(str)
    track_state_changed = Signal(bool)

    def __init__(
        self,
        server: str = "http://localhost:13091",
        update_time: int = 1000,
        parent=None,
        objectName=None,
    ):
        super().__init__(parent, objectName=objectName)

        self._track: str | None = None
        self._artist: str | None = None
        self._playing: bool = False

        if server.endswith("/"):
            server = server[:-1]

        self._server = server
        self._active_requests: dict[str, QNetworkReply] = {}
        self._timer = QTimer(self, interval=update_time)
        self._timer.timeout.connect(self._update_status)
        self._network_manager = QRestAccessManager(QNetworkAccessManager(self))

    @property
    def playing(self) -> bool:
        return self._playing

    @playing.setter
    def playing(self, value: bool):
        if self._playing == value:
            return

        self._playing = value
        self.track_state_changed.emit(value)

    @property
    def track(self) -> str | None:
        return self._track

    @track.setter
    def track(self, value: str):
        if self._track == value:
            return

        self._track = value
        self.track_changed.emit(value)

    @property
    def artist(self) -> str | None:
        return self._artist

    @artist.setter
    def artist(self, value: str):
        if self._artist == value:
            return

        self._artist = value
        self.artist_changed.emit(value)

    def start(self):
        self._timer.start(1000)

    def stop(self):
        self._timer.stop()

    @Slot()
    def prev_track(self):
        self._post_request("track/prev", {}, lambda reply: self._update_status())

    @Slot()
    def next_track(self):
        self._post_request("track/next", {}, lambda reply: self._update_status())

    @Slot()
    def toggle_play_pause(self):
        if self.playing:
            endpoint = "track/pause"
        else:
            endpoint = "track/play"

        if self._post_request(endpoint, {}, self._handle_play_pause_reply):
            self.playing = not self.playing

    @Slot()
    def play(self):
        if not self.playing:
            self.toggle_play_pause()

    @Slot()
    def pause(self):
        if self.playing:
            self.toggle_play_pause()

    @Slot()
    def _update_status(self):
        self._get_request("track", self._handle_track_reply)
        self._get_request("track/state", self._handle_state_reply)

    def _has_active_request(self, endpoint: str) -> bool:
        if endpoint in self._active_requests:
            reply = self._active_requests[endpoint]
            finished = True
            try:
                finished = reply.isFinished()
            except RuntimeError as ex:
                pass

            if not finished:
                return True

            del self._active_requests[endpoint]
        return False

    def _get_request(
        self, endpoint: str, slot: typing.Callable[..., typing.Any]
    ) -> QNetworkReply | None:
        url = f"{self._server}/{endpoint}"
        _logger.debug(f"Requested GET request for {url}")
        if self._has_active_request(endpoint):
            _logger.debug(f"Request for {url} already in progress... ignoring")
            return None

        _logger.debug(f"Sending GET request for {url}")
        reply = self._network_manager.get(QNetworkRequest(url), self, slot)
        self._active_requests[endpoint] = reply
        return reply

    def _post_request(
        self,
        endpoint: str,
        data: dict[str, typing.Any],
        slot: typing.Callable[..., typing.Any],
    ) -> QNetworkReply | None:
        url = f"{self._server}/{endpoint}"
        _logger.debug(f"Requested POST request for {url}")
        if self._has_active_request(endpoint):
            _logger.debug(f"Request for {url} already in progress... ignoring")
            return None

        _logger.debug(f"Sending POST request for {url}")
        reply = self._network_manager.post(QNetworkRequest(url), data, self, slot)
        self._active_requests[endpoint] = reply
        return reply

    def _handle_track_reply(self, reply: QRestReply):
        if reply.isSuccess():
            data = json.loads(reply.readText())
            if "video" in data:
                video_data = data["video"]
                if "title" in video_data:
                    title = video_data["title"]
                    if self._track != title:
                        self._track = title
                        self.track_changed.emit(title)

                if "author" in video_data:
                    artist = video_data["author"]
                    if self._artist != artist:
                        self._artist = artist
                        self.artist_changed.emit(artist)
        else:
            _logger.warning(f"Failed to get track: {reply.errorString()}")

    def _handle_state_reply(self, reply: QRestReply):
        if reply.isSuccess():
            data = json.loads(reply.readText())
            if "playing" in data:
                playing = data["playing"]
                if self._playing != playing:
                    self._playing = playing
                    self.track_state_changed.emit(playing)
        else:
            _logger.warning(f"Failed to get state: {reply.errorString()}")

    def _handle_play_pause_reply(self, reply: QRestReply):
        if reply.isSuccess():
            data = json.loads(reply.readText())
            if "isPlaying" in data:
                playing = data["isPlaying"]
                if self._playing != playing:
                    self._playing = playing
                    self.track_state_changed.emit(playing)
        else:
            _logger.warning(f"Failed to toggle play/pause: {reply.errorString()}")
