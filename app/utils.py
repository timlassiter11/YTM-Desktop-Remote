# If we don't import QtSvg,
# the get_themed_icon function doesn't work.
from PySide6 import QtSvg
from PySide6.QtCore import Qt, QFile
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap, QTransform
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


def rotate_pixmap(pixmap: QPixmap, angle: float):
    """Rotates a QPixmap by the given angle (in degrees)."""
    transform = QTransform().rotate(angle)
    rotated_pixmap = pixmap.transformed(
        transform, Qt.TransformationMode.SmoothTransformation
    )
    return rotated_pixmap


def rotate_icon(icon: QIcon, angle: float) -> QIcon:
    """Rotates a QIcon by the given angle (in degrees)."""
    pixmap = icon.pixmap(icon.availableSizes()[0])  # Get the pixmap
    rotated_pixmap = rotate_pixmap(pixmap, angle)
    return QIcon(rotated_pixmap)
