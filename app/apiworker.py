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
    title_changed = Signal(str)
    artist_changed = Signal(str)
    play_state_changed = Signal(bool)
    like_state_changed = Signal(bool)
    dislike_state_changed = Signal(bool)

    def __init__(
        self,
        server: str = "http://localhost:13091",
        update_time: int = 1000,
        parent=None,
        objectName=None,
    ):
        super().__init__(parent, objectName=objectName)

        if server.endswith("/"):
            server = server[:-1]
        self._server = server

        self._title: str | None = None
        self._artist: str | None = None
        self._playing: bool = False
        self._liked: bool = False
        self._disliked: bool = False

        self._active_requests: dict[str, QNetworkReply] = {}
        self._timer = QTimer(self, interval=update_time)
        self._timer.timeout.connect(self._update_status)
        self._network_manager = QRestAccessManager(QNetworkAccessManager(self))

    @property
    def playing(self) -> bool:
        return self._playing

    @property
    def title(self) -> str | None:
        return self._title

    @property
    def artist(self) -> str | None:
        return self._artist

    @property
    def liked(self) -> bool:
        return self._liked

    @property
    def disliked(self) -> bool:
        return self._disliked

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
    def toggle_like_track(self):
        self._post_request("track/like", {}, lambda reply: self._update_status())

    @Slot()
    def toggle_dislike_track(self):
        self._post_request("track/dislike", {}, lambda reply: self._update_status())

    @Slot()
    def toggle_play_pause(self):
        if self._playing:
            endpoint = "track/pause"
        else:
            endpoint = "track/play"

        if self._post_request(endpoint, {}, self._handle_play_pause_reply):
            self._update_play_state(not self._playing)

    @Slot()
    def play(self):
        if not self._playing:
            self.toggle_play_pause()

    @Slot()
    def pause(self):
        if self._playing:
            self.toggle_play_pause()

    @Slot()
    def _update_status(self):
        self._get_request("track", self._handle_track_reply)
        self._get_request("track/state", self._handle_state_reply)

    def _update_track_info(self, title: str | None, artist: str | None):
        if title != self._title or artist != self._artist:
            self._title = title
            self._artist = artist
            self.title_changed.emit()

    def _update_play_state(self, playing: bool):
        if playing != self._playing:
            self._playing = playing
            self.play_state_changed.emit()

    def _update_like_state(self, like: bool, dislike: bool):
        if like != self._liked or dislike != self._disliked:
            self._liked = like
            self._disliked = dislike
            self.like_state_changed.emit()

    def _has_active_request(self, endpoint: str) -> bool:
        if endpoint in self._active_requests:
            reply = self._active_requests[endpoint]
            finished = True
            try:
                finished = reply.isFinished()
            except RuntimeError as ex:
                # Fixes C++ object deleted bug
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
            title = self._title
            artist = self._artist
            if "video" in data:
                video_data = data["video"]
                if "title" in video_data:
                    title = video_data["title"]
                    if title != self._title:
                        self._title = title
                        self.title_changed.emit(title)

                if "author" in video_data:
                    artist = video_data["author"]
                    if artist != self._artist:
                        self._artist = artist
                        self.artist_changed.emit(artist)
        else:
            _logger.warning(f"Failed to get track: {reply.errorString()}")

    def _handle_state_reply(self, reply: QRestReply):
        if reply.isSuccess():
            data = json.loads(reply.readText())
            playing = self._playing
            like = self._liked
            dislike = self._disliked
            if "playing" in data:
                playing = data["playing"]
                if playing != self._playing:
                    self._playing = playing
                    self.play_state_changed.emit(playing)
                    

            if "liked" in data:
                like = data["liked"]
                if like != self._liked:
                    self._liked = like
                    self.like_state_changed.emit(like)
                    
            if "disliked" in data:
                dislike = data["disliked"]
                if dislike != self._disliked:
                    self._disliked = dislike
                    self.dislike_state_changed.emit(dislike)
        else:
            _logger.warning(f"Failed to get state: {reply.errorString()}")

    def _handle_play_pause_reply(self, reply: QRestReply):
        if reply.isSuccess():
            data = json.loads(reply.readText())
            if "isPlaying" in data:
                playing = data["isPlaying"]
                if playing != self._playing:
                    self._playing = playing
                    self.play_state_changed.emit(playing)
        else:
            _logger.warning(f"Failed to toggle play/pause: {reply.errorString()}")
