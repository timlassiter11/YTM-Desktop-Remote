from gettext import install
import json
import logging
import typing

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtGui import QPixmap
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
    artwork_changed = Signal(QPixmap)

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
        self._artwork_url: str | None = None
        self._artwork: QPixmap | None = None

        self._active_requests: dict[str, QNetworkReply] = {}
        self._timer = QTimer(self, interval=update_time)
        self._timer.timeout.connect(lambda: self._update_status())
        self._network_manager = QRestAccessManager(QNetworkAccessManager(self))

    @property
    def playing(self) -> bool:
        return self._playing
    
    @playing.setter
    def playing(self, value: bool):
        if value != self._playing:
            self._playing = value
            self.play_state_changed.emit(value)
        
    @property
    def title(self) -> str | None:
        return self._title
    
    @title.setter
    def title(self, value: str):
        if value != self._title:
            self._title = value
            self.title_changed.emit(value)

    @property
    def artist(self) -> str | None:
        return self._artist
    
    @artist.setter
    def artist(self, value: str):
        if value != self._artist:
            self._artist = value
            self.artist_changed.emit(value)
            
    @property
    def liked(self) -> bool:
        return self._liked
    
    @liked.setter
    def liked(self, value: bool):
        if value != self._liked:
            self._liked = value
            self.like_state_changed.emit(value)
            
    @property
    def disliked(self) -> bool:
        return self._disliked
    
    @disliked.setter
    def disliked(self, value: bool):
        if value != self._disliked:
            self._disliked = value
            self.dislike_state_changed.emit(value)

    @property
    def artwork(self) -> QPixmap | None:
        return self._artwork
    
    @artwork.setter
    def artwork(self, value: QPixmap):
        self._artwork = value
        self.artwork_changed.emit(value)
            
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
        if self._post_request("track/like", {}, lambda reply: self._update_status()):
            self.liked = not self._liked

    @Slot()
    def toggle_dislike_track(self):
        if self._post_request("track/dislike", {}, lambda reply: self._update_status()):
            self.disliked = not self._disliked
            
    @Slot()
    def toggle_play_pause(self):
        if self._playing:
            endpoint = "track/pause"
        else:
            endpoint = "track/play"

        if self._post_request(endpoint, {}, self._handle_play_pause_reply):
            self.playing = not self._playing

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
        try:
            if reply.isSuccess():
                text = reply.readText()
                data = json.loads(text)
                if not data:
                    return

                if "video" in data:
                    video_data = data["video"]
                    if "title" in video_data:
                        self.title = video_data["title"]

                    if "author" in video_data:
                        self.artist = video_data["author"]

                    if "thumbnail" in video_data:
                        if "thumbnails" in video_data["thumbnail"]:
                            thumbnails = video_data["thumbnail"]["thumbnails"]
                            if isinstance(thumbnails, list) and thumbnails:
                                url = thumbnails[0]["url"]
                                if url != self._artwork_url:
                                    self._artwork_url = url
                                    self._network_manager.get(QNetworkRequest(url), self, self._handle_artwork_reply)
            else:
                _logger.warning(f"Failed to get track: {reply.errorString()}")
        except Exception as ex:
            _logger.exception(ex)
            
    def _handle_state_reply(self, reply: QRestReply):
        try:
            if reply.isSuccess():
                text = reply.readText()
                data = json.loads(text)
                if not data:
                    return

                if "playing" in data:
                    self.playing = data["playing"]

                if "liked" in data:
                    self.liked = data["liked"]

                if "disliked" in data:
                    self.disliked = data["disliked"]
            else:
                _logger.warning(f"Failed to get state: {reply.errorString()}")
        except Exception as ex:
            _logger.exception(ex)

    def _handle_play_pause_reply(self, reply: QRestReply):
        try:
            if reply.isSuccess():
                text = reply.readText()
                data = json.loads(text)
                if not data:
                    return
                
                if "isPlaying" in data:
                    self.playing = data["isPlaying"]
            else:
                _logger.warning(f"Failed to toggle play/pause: {reply.errorString()}")
        except Exception as ex:
            _logger.exception(ex)

    def _handle_artwork_reply(self, reply: QRestReply):
        try:
            if reply.isSuccess():
                pixmap = QPixmap()
                pixmap.loadFromData(reply.readBody())
                self.artwork = pixmap
            else:
                _logger.warning(f"Failed to get artwork: {reply.errorString()}")
        except Exception as ex:
            _logger.exception(ex)