import math

from PyQt6.QtCore import pyqtSignal, QPointF, QSize, Qt
from PyQt6.QtGui import QPainter, QPixmap, QColor, QPolygonF, QMouseEvent, QBrush
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

    def __init__(self, pixmap=None, parent=None, data=None, delegate=None, border=0):
        super().__init__(parent)
        if pixmap is None:
            pixmap = QPixmap(50, 50)
            pixmap.fill(PicButton._next())
        elif isinstance(pixmap, str):
            pixmap = QPixmap(pixmap)
        self.pixmap = pixmap
        self.data = data
        self.border = border
        self.delegate = delegate
        self.setCheckable(True)
        self.setChecked(False)
        self.setAutoExclusive(True)

    def paintEvent(self, event):
        rect = event.rect()
        painter = QPainter(self)
        if self.border > 0:
            c = QColor('red' if self.isChecked() else 'green')
            painter.setBrush(QBrush(c))
            painter.drawRect(rect)
            rect.adjust(self.border, self.border, -self.border, -self.border)
        painter.drawPixmap(rect, self.pixmap)

    def sizeHint(self):
        size = self.pixmap.size()
        size += QSize(self.border*2, self.border*2)
        return size


class PicGrid(QWidget):
    selec = pyqtSignal(object)

    def delegate(self, obj):
        self.selec.emit(obj)

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        if data is not None:
            self.set_data(data)

    def set_data(self, data):
        layout = QGridLayout(self)
        layout.setSpacing(0)
        self.array = []
        self.dict = {}
        for row, r in enumerate(data):
            for col, c in enumerate(r):
                if isinstance(c, dict):
                    pb = PicButton(c.get('file'), delegate=self.delegate, data=c, border=3)
                else:
                    pb = PicButton(c, delegate=self.delegate, data=c, border=3)
                if pb is not None:
                    layout.addWidget(pb, row, col)
                    self.array.append(pb)
                    self.dict[c] = pb

    def select(self, idx):
        self.array[idx-1].setChecked(True)


class StarRating(object):
    """ Handle the actual painting of the stars themselves. """

    PAINTING_SCALE_FACTOR = 20

    def __init__(self, star_count=1, max_star_count=5):
        self.star_count = star_count
        self.MAX_STAR_COUNT = max_star_count

        # Create the star shape we'll be drawing.
        self._star_polygon = QPolygonF()
        self._star_polygon.append(QPointF(1.0, 0.5))
        for i in range(1, 5):
            self._star_polygon.append(QPointF(0.5 + 0.5 * math.cos(0.8 * i * math.pi),
                                              0.5 + 0.5 * math.sin(0.8 * i * math.pi)))

        # Create the diamond shape we'll show in the editor
        self._diamond_polygon = QPolygonF()
        diamond_points = [QPointF(0.4, 0.5), QPointF(0.5, 0.4),
                          QPointF(0.6, 0.5), QPointF(0.5, 0.6),
                          QPointF(0.4, 0.5)]
        for dp in diamond_points:
            self._diamond_polygon.append(dp)

    def sizeHint(self):
        """ Tell the caller how big we are. """
        return self.PAINTING_SCALE_FACTOR * QSize(self.MAX_STAR_COUNT, 1)

    def paint(self, painter, rect, palette, is_editable=False):
        """ Paint the stars (and/or diamonds if we're in editing mode). """
        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)

        if is_editable:
            painter.setBrush(palette.highlight())
        else:
            painter.setBrush(palette.windowText())

        y_offset = (rect.height() - self.PAINTING_SCALE_FACTOR) / 2
        painter.translate(rect.x(), rect.y() + y_offset)
        painter.scale(self.PAINTING_SCALE_FACTOR, self.PAINTING_SCALE_FACTOR)

        for i in range(self.MAX_STAR_COUNT):
            if i < self.star_count:
                painter.drawPolygon(self._star_polygon, Qt.FillRule.WindingFill)
            elif is_editable:
                painter.drawPolygon(self._diamond_polygon, Qt.FillRule.WindingFill)
            painter.translate(1.0, 0.0)

        painter.restore()


class StarEditor(QWidget):
    """ The custom editor for editing StarRatings. """

    # A signal to tell the delegate when we've finished editing.
    editing_finished = pyqtSignal(int)

    def __init__(self, parent=None, max_count=9, count=1):
        """ Initialize the editor object, making sure we can watch mouse
            events.
        """
        super().__init__(parent)

        self.rating = None
        self.setMouseTracking(True)
        self.setAutoFillBackground(True)
        self.star_rating = StarRating(star_count=count, max_star_count=max_count)

    def set_stars(self, max_count, count):
        self.star_rating = StarRating(star_count=count, max_star_count=max_count)

    def sizeHint(self):
        """ Tell the caller how big we are. """
        return self.star_rating.sizeHint()

    def paintEvent(self, event):
        """ Paint the editor, offloading the work to the StarRating class. """
        with QPainter(self) as painter:
            self.star_rating.paint(painter, self.rect(), self.palette(), is_editable=True)

    def enterEvent(self, event):
        self.rating = self.star_rating.star_count

    def leaveEvent(self, a0):
        self.star_rating.star_count = self.rating
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        """ As the mouse moves inside the editor, track the position and
            update the editor to display as many stars as necessary.
        """
        star = self.star_at_position(event.position().x())

        if (star != self.star_rating.star_count) and (star != -1):
            self.star_rating.star_count = star
            self.update()

    def mouseReleaseEvent(self, event):
        """ Once the user has clicked his/her chosen star rating, tell the
            delegate we're done editing.
        """
        self.rating = self.star_rating.star_count
        self.editing_finished.emit(self.rating)

    def star_at_position(self, x):
        """ Calculate which star the user's mouse cursor is currently
            hovering over.
        """
        star = int(x / (self.star_rating.sizeHint().width() /
                        self.star_rating.MAX_STAR_COUNT)) + 1
        if (star <= 0) or (star > self.star_rating.MAX_STAR_COUNT):
            return -1

        return star

    def set_stars(self, stars):
        self.star_rating.star_count = stars


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QVBoxLayout
    import sys


    class MainWindow(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setWindowTitle('Vocations')

            layout = QVBoxLayout()
            self.setLayout(layout)
            self.vo = PicGrid(
                [['resources/DDicon_fighter.webp', 'resources/DDicon_strider.webp', 'resources/DDicon_mage.webp'],
                 ['resources/DDicon_assassin.webp', 'resources/DDicon_magicarcher.webp', 'resources/DDicon_magicknight.webp'],
                 ['resources/DDicon_warrior.webp', 'resources/DDicon_ranger.webp', 'resources/DDicon_sorcerer.webp']
                 ])
            layout.addWidget(self.vo)


    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
