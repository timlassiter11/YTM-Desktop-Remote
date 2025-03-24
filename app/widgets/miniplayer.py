import qtawesome as qta  # type: ignore
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget

from app.ui import ui_miniplayer


class MiniPlayerWidget(QWidget):
    play_pause_triggered = Signal()
    next_triggered = Signal()
    prev_triggered = Signal()
    like_triggered = Signal()
    dislike_triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = ui_miniplayer.Ui_MiniPlayer()
        self.ui.setupUi(self)
        self.setFixedWidth(300)

        self.ui.playButton.setIcon(qta.icon("mdi.play"))
        self.ui.nextButton.setIcon(qta.icon("mdi.skip-next"))
        self.ui.previousButton.setIcon(qta.icon("mdi.skip-previous"))
        self.ui.likeButton.setIcon(qta.icon("mdi.thumb-up-outline"))
        self.ui.dislikeButton.setIcon(qta.icon("mdi.thumb-down-outline"))

        self.ui.playButton.clicked.connect(self.play_pause_triggered)
        self.ui.nextButton.clicked.connect(self.next_triggered)
        self.ui.previousButton.clicked.connect(self.prev_triggered)
        self.ui.likeButton.clicked.connect(self.like_triggered)
        self.ui.dislikeButton.clicked.connect(self.dislike_triggered)

        self._hide_timer = QTimer(self, interval=5000, singleShot=True)
        self._hide_timer.timeout.connect(self.hide)

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setWidth(300)
        return hint

    def setTitle(self, title: str):
        self.ui.titleLabel.setText(title)

    def setArtist(self, artist: str):
        self.ui.artistLabel.setText(artist)

    def setPlayState(self, playing: bool):
        self.ui.playButton.setIcon(qta.icon("mdi.pause" if playing else "mdi.play"))

    def setLikeState(self, liked: bool):
        self.ui.likeButton.setIcon(
            qta.icon("mdi.thumb-up" if liked else "mdi.thumb-up-outline")
        )

    def setDislikeState(self, disliked: bool):
        self.ui.dislikeButton.setIcon(
            qta.icon("mdi.thumb-down" if disliked else "mdi.thumb-down-outline")
        )

    def setArtwork(self, artwork: QPixmap):
        self.ui.artworkLabel.setPixmap(artwork)

    def showEvent(self, event):
        self._hide_timer.start()
        super().showEvent(event)

    def enterEvent(self, event):
        self._hide_timer.stop()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self._hide_timer.start()
        return super().leaveEvent(event)