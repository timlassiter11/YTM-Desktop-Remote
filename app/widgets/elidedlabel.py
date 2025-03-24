from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QPainter
from PySide6.QtWidgets import QLabel


class ElidedLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._elided_text = ""

    def setText(self, text):
        self._text = text
        self.setToolTip(text)
        self.update_elided_text()
        super().setText(self._elided_text)

    def update_elided_text(self):
        font_metrics = QFontMetrics(self.font())
        available_width = self.width()
        self._elided_text = font_metrics.elidedText(
            self._text, Qt.TextElideMode.ElideRight, available_width
        )
        super().setText(self._elided_text)

    def resizeEvent(self, event):
        self.update_elided_text()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawText(
            0,
            (self.height() - painter.fontMetrics().height()) / 2
            + painter.fontMetrics().ascent(),
            self._elided_text,
        )
