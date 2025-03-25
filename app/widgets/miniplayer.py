import qtawesome as qta  # type: ignore
from PySide6.QtCore import QCoreApplication, Qt, QTimer, Signal, Slot, QPoint
from PySide6.QtGui import QIcon, QPixmap, QMouseEvent, QHideEvent
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from app.ui import ui_miniplayer


class MiniPlayerWidget(QWidget):
    playPauseTriggered = Signal()
    nextTriggered = Signal()
    previousTriggered = Signal()
    likeTriggered = Signal()
    dislikeTriggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Popup)
        

        self.ui = ui_miniplayer.Ui_MiniPlayer()
        self.ui.setupUi(self)

        menu = QMenu(self)

        exit_action = menu.addAction("Exit")
        exit_action.setIcon(qta.icon("mdi.close"))
        exit_action.triggered.connect(QCoreApplication.quit)

        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setContextMenu(menu)
        self._tray_icon.activated.connect(self._tray_activated)

        icon = QIcon(":/icons/icon.png")
        self._tray_icon.setIcon(icon)
        self.setWindowIcon(icon)

        self.ui.artworkLabel.setFixedSize(64, 64)
        self.setFixedWidth(300)

        self.ui.closeButton.setIcon(qta.icon("mdi.close"))
        self.ui.playButton.setIcon(qta.icon("mdi.play"))
        self.ui.nextButton.setIcon(qta.icon("mdi.skip-next"))
        self.ui.previousButton.setIcon(qta.icon("mdi.skip-previous"))
        self.ui.likeButton.setIcon(qta.icon("mdi.thumb-up-outline"))
        self.ui.dislikeButton.setIcon(qta.icon("mdi.thumb-down-outline"))

        self.ui.closeButton.clicked.connect(self.hide)
        self.ui.playButton.clicked.connect(self.playPauseTriggered)
        self.ui.nextButton.clicked.connect(self.nextTriggered)
        self.ui.previousButton.clicked.connect(self.previousTriggered)
        self.ui.likeButton.clicked.connect(self.likeTriggered)
        self.ui.dislikeButton.clicked.connect(self.dislikeTriggered)

        self._hide_timer = QTimer(self, interval=5000, singleShot=True)
        self._hide_timer.timeout.connect(self.hide)
        self._tray_icon.show()

        self._dragging = False
        self._drag_position = QPoint()
        self._set_keep_open(False)

    @Slot(str)  # type: ignore
    def setTitle(self, title: str):
        self.ui.titleLabel.setText(title)
        self._update_tooltip()

    @Slot(str)  # type: ignore
    def setArtist(self, artist: str):
        self.ui.artistLabel.setText(artist)
        self._update_tooltip()

    @Slot(bool)  # type: ignore
    def setPlaying(self, playing: bool):
        self.ui.playButton.setIcon(qta.icon("mdi.pause" if playing else "mdi.play"))

    @Slot(bool)  # type: ignore
    def setLiked(self, liked: bool):
        self.ui.likeButton.setIcon(
            qta.icon("mdi.thumb-up" if liked else "mdi.thumb-up-outline")
        )

    @Slot(bool)  # type: ignore
    def setDisliked(self, disliked: bool):
        self.ui.dislikeButton.setIcon(
            qta.icon("mdi.thumb-down" if disliked else "mdi.thumb-down-outline")
        )

    @Slot(QPixmap)  # type: ignore
    def setArtwork(self, artwork: QPixmap):
        self.ui.artworkLabel.setPixmap(artwork)

    def _set_keep_open(self, keep_open: bool):
        self.setWindowFlag(Qt.WindowType.Dialog, keep_open)
        self._hide_timer.blockSignals(keep_open)
        if keep_open:
            self.show()

    def _update_tooltip(self):
        title = self.ui.titleLabel.text()
        artist = self.ui.artistLabel.text()
        self._tray_icon.setToolTip(f"{title}\n{artist}")

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if not self.isVisible():
                self._set_keep_open(False)
                pos = self._tray_icon.geometry().topRight()
                size = self.sizeHint()
                self.move(pos.x() - size.width(), pos.y() - size.height())
                self.show()
            else:
                self.hide()

    def showEvent(self, event):
        self._hide_timer.start()
        
    def enterEvent(self, event):
        self._hide_timer.stop()

    def leaveEvent(self, event):
        self._hide_timer.start()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.geometry().topLeft()
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_position:
            new_position = event.globalPosition().toPoint() - self._drag_position
            self._dragging = True
            self.move(new_position)
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self._dragging = False
                self._set_keep_open(True)

            event.accept()
        else:
            event.ignore()

    def mouseDoubleClickEvent(self, event):
        self._set_keep_open(True)
    
    
    