import json
import logging
import typing

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot
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
    titleChanged = Signal(str)
    artistChanged = Signal(str)
    playingChanged = Signal(bool)
    likedChanged = Signal(bool)
    dislikedChanged = Signal(bool)
    artworkChanged = Signal(QPixmap)

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

    def isPlaying(self) -> bool:
        return self._playing

    def setPlaying(self, value: bool):
        if value != self._playing:
            self._playing = value
            self.playingChanged.emit(value)

    def title(self) -> str | None:
        return self._title

    def setTitle(self, value: str):
        if value != self._title:
            self._title = value
            self.titleChanged.emit(value)

    def artist(self) -> str | None:
        return self._artist

    def setArtist(self, value: str):
        if value != self._artist:
            self._artist = value
            self.artistChanged.emit(value)

    def isLiked(self) -> bool:
        return self._liked

    def setLiked(self, value: bool):
        if value != self._liked:
            self._liked = value
            self.likedChanged.emit(value)

    def isDisliked(self) -> bool:
        return self._disliked

    def setDisliked(self, value: bool):
        if value != self._disliked:
            self._disliked = value
            self.dislikedChanged.emit(value)

    def artwork(self) -> QPixmap | None:
        return self._artwork

    def setArtwork(self, value: QPixmap):
        self._artwork = value
        self.artworkChanged.emit(value)

    def start(self):
        self._timer.start(1000)

    def stop(self):
        self._timer.stop()

    @Slot()
    def requestPreviousTrack(self):
        self._post_request("track/prev", {}, lambda reply: self._update_status())

    @Slot()
    def requestNextTrack(self):
        self._post_request("track/next", {}, lambda reply: self._update_status())

    @Slot()
    def requestToggleLike(self):
        if self._post_request("track/like", {}, lambda reply: self._update_status()):
            self.setLiked(not self._liked)

    @Slot()
    def requestToggleDislike(self):
        if self._post_request("track/dislike", {}, lambda reply: self._update_status()):
            self.setDisliked(not self._disliked)

    @Slot()
    def requestTogglePlayPause(self):
        if self._playing:
            endpoint = "track/pause"
        else:
            endpoint = "track/play"

        if self._post_request(endpoint, {}, self._handle_play_pause_reply):
            self.isPlaying = not self._playing

    @Slot()
    def requestPlay(self):
        if not self._playing:
            self.requestTogglePlayPause()

    @Slot()
    def requestPause(self):
        if self._playing:
            self.requestTogglePlayPause()

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
                        self.setTitle(video_data["title"])

                    if "author" in video_data:
                        self.setArtist(video_data["author"])

                    if "thumbnail" in video_data:
                        if "thumbnails" in video_data["thumbnail"]:
                            thumbnails = video_data["thumbnail"]["thumbnails"]
                            if isinstance(thumbnails, list) and thumbnails:
                                url = thumbnails[0]["url"]
                                if url != self._artwork_url:
                                    self._artwork_url = url
                                    self._network_manager.get(
                                        QNetworkRequest(url),
                                        self,
                                        self._handle_artwork_reply,
                                    )
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
                    self.setPlaying(data["playing"])

                if "liked" in data:
                    self.setLiked(data["liked"])

                if "disliked" in data:
                    self.setDisliked(data["disliked"])
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
                    self.setPlaying(data["isPlaying"])
            else:
                _logger.warning(f"Failed to toggle play/pause: {reply.errorString()}")
        except Exception as ex:
            _logger.exception(ex)

    def _handle_artwork_reply(self, reply: QRestReply):
        try:
            if reply.isSuccess():
                pixmap = QPixmap()
                pixmap.loadFromData(reply.readBody())
                self.setArtwork(pixmap)
            else:
                _logger.warning(f"Failed to get artwork: {reply.errorString()}")
        except Exception as ex:
            _logger.exception(ex)


    isPlaying = Property(bool, isPlaying, setPlaying, notify=playingChanged) # type: ignore
    title = Property(str, title, setTitle, notify=titleChanged) # type: ignore
    artist = Property(str, artist, setArtist, notify=artistChanged) # type: ignore
    isLiked = Property(bool, isLiked, setLiked, notify=likedChanged) # type: ignore
    isDisliked = Property(bool, isDisliked, setDisliked, notify=dislikedChanged) # type: ignore
    artwork = Property(QPixmap, artwork, setArtwork, notify=artworkChanged) # type: ignore