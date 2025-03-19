# If we don't import QtSvg,
# the get_themed_icon function doesn't work.
from PySide6 import QtSvg
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import QApplication

def get_themed_icon(svg_filepath, color: QColor | None = None) -> QIcon:
    if color is None:
        color = QApplication.palette().color(QPalette.ColorRole.WindowText)

    img = QPixmap(svg_filepath)
    qp = QPainter(img)
    qp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    qp.fillRect(img.rect(), color)
    qp.end()
    return QIcon(img)
