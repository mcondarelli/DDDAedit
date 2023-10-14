from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QPixmap, QColor
from PyQt6.QtWidgets import QAbstractButton, QWidget, QGridLayout


class PicButton(QAbstractButton):
    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if self.delegate is not None and self.underMouse():
            self.delegate(self.data)

    _names = QColor.colorNames()
    _currc = 0

    @staticmethod
    def _next():
        PicButton._currc += 1
        if PicButton._currc >= len(PicButton._names):
            PicButton._currc = 0
        cname = PicButton._names[PicButton._currc]
        return QColor(cname)

    def __init__(self, pixmap=None, parent=None, data=None, delegate=None):
        super().__init__(parent)
        if pixmap is None:
            pixmap = QPixmap(50, 50)
            pixmap.fill(PicButton._next())
        elif isinstance(pixmap, str):
            pixmap = QPixmap(pixmap)
        self.pixmap = pixmap
        self.data = data
        self.delegate = delegate

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()


class PicGrid(QWidget):
    selec = pyqtSignal(object)

    def delegate(self, obj):
        self.selec.emit(obj)

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        data = data or [[None, None, None], [None, None, None], [None, None, None]]
        layout = QGridLayout(self)
        for row, r in enumerate(data):
            for col, c in enumerate(r):
                if isinstance(c, dict):
                    pb = PicButton(c.get('file'), delegate=self.delegate, data=c)
                else:
                    pb = PicButton(c, delegate=self.delegate, data=c)
                if pb is not None:
                    layout.addWidget(pb, row, col)

