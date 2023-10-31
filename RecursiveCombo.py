from PyQt6.QtCore import pyqtSignal, QModelIndex, Qt, QSize, QPoint, QAbstractProxyModel
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtWidgets import QToolButton, QSizePolicy, QListView, QStyle


class RecursiveCombo(QToolButton):
    _placeholderText = ''
    indexChanged = pyqtSignal([QModelIndex], [str])

    def __init__(self, placeholderText='Select option', data=None):
        self._currentIndex = None
        super().__init__(text=placeholderText)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setStyleSheet('''
            AlternateCombo { 
                border: none; 
            }
            AlternateCombo::pressed {
                border: 1px inset palette(shadow);
                border-radius: 2px;
                background: palette(dark);
            }
        ''')
        self.popup = QListView(self)
        self.popup.setWindowFlags(Qt.WindowType.Popup)
        self.popup.setEditTriggers(self.popup.EditTrigger.NoEditTriggers)
        self.popup.setSizeAdjustPolicy(self.popup.SizeAdjustPolicy.AdjustToContents)
        self.popup.installEventFilter(self)
        sz = self.fontMetrics().height() - 4
        self.popup.setIconSize(QSize(sz, sz))
        self.model = QStandardItemModel()
        self.popup.setModel(self.model)

        self.clicked.connect(self.showPopup)
        self.popup.clicked.connect(self.itemClicked)
        self.popup.activated.connect(self.itemClicked)

        if data is not None:
            self.setData(data)

    def _emitIndexChanged(self, index):
        self.indexChanged.emit(index)
        self.indexChanged[str].emit(index.data())

    def _itemSizeHint(self):
        return QSize(-1,
            self.fontMetrics().height() +
            self.style().pixelMetric(
                QStyle.PixelMetric.PM_LayoutVerticalSpacing)
        )

    def setData(self, data, parent=None):
        if parent is None:
            self.model.clear()
            parent = self.model.invisibleRootItem()
            self._currentIndex = QModelIndex()
        hint = self._itemSizeHint()
        for k, v in data.items():
            item = QStandardItem(k)
            item.setSizeHint(hint)
            parent.appendRow(item)
            if isinstance(v, dict):
                item.setIcon(self.style().standardIcon(
                    QStyle.StandardPixmap.SP_ArrowRight))
                sep = QStandardItem('..')
                sep.setIcon(self.style().standardIcon(
                    QStyle.StandardPixmap.SP_ArrowLeft))
                sep.setSizeHint(hint)
                sep.setData(True, Qt.ItemDataRole.UserRole)
                item.appendRow(sep)
                self.setData(v, item)

    def copyModel(self, model: QStandardItemModel):
        self.model.clear()
        hint = self._itemSizeHint()
        self._currentIndex = QModelIndex()

        def recurse(dest, parent=QModelIndex()):
            for n in range(model.rowCount(parent)):
                index = model.index(n, 0, parent)
                k = model.data(index)
                item = QStandardItem(k)
                item.setSizeHint(hint)
                dest.appendRow(item)
                if model.hasChildren(index):
                    item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
                    sep = QStandardItem('..')
                    sep.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
                    sep.setSizeHint(hint)
                    sep.setData(True, Qt.ItemDataRole.UserRole)
                    item.appendRow(sep)
                    recurse(item, index)
        recurse(self.model.invisibleRootItem())

    def setModel(self, model: QStandardItemModel):
        # FIXME: shouid invalidate model?
        self.model = model
        self.popup.setModel(self.model)
        self.reset_model()
        self.model.modelReset.connect(self.reset_model)

    def reset_model(self):
        def recurse(mod: QStandardItemModel, par=QModelIndex()):
            for n in range(mod.rowCount(par)):
                idx = mod.index(n, 0, par)
                src = None
                if isinstance(mod, QAbstractProxyModel):
                    src = mod.mapToSource(idx)
                    itm = mod.sourceModel().itemFromIndex(src)
                else:
                    itm = mod.itemFromIndex(idx)
                itm.setSizeHint(hint)
                itm.setFlags(itm.flags() | Qt.ItemFlag.ItemIsEnabled)
                if mod.hasChildren(idx):
                    itm.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
                    recurse(mod, idx)
                else:
                    itm.setIcon(QIcon())
                    if src is not None:
                        if mod.sourceModel().hasChildren(src):
                            itm.setFlags(itm.flags() & ~Qt.ItemFlag.ItemIsEnabled)

        hint = self._itemSizeHint()
        self._currentIndex = QModelIndex()
        recurse(self.model)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress:
            self.popup.hide()
            return True
        elif event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Right:
                current = self.popup.currentIndex()
                if current.isValid() and self.model.hasChildren(current):
                    self.itemClicked(current)
                    return True
            elif key == Qt.Key.Key_Left:
                parent = self.popup.rootIndex()
                if parent.isValid():
                    self.setPopupRoot(parent.parent())
                    self.popup.setCurrentIndex(parent)
                    return True
        return super().eventFilter(obj, event)

    def showPopup(self):
        self.setPopupRoot(QModelIndex())
        self.popup.move(self.mapToGlobal(QPoint()))
        self.popup.show()

    def setPopupRoot(self, parent):
        self.popup.setRootIndex(parent)

        if self._currentIndex.isValid():
            # highlight the current index (or any of its parent)
            index = self._currentIndex
            currentParent = index.parent()
            while currentParent != parent:
                index = currentParent
                currentParent = index.parent()
                if not currentParent.isValid():
                    index = self.model.index(0, 0, parent)
                    break
        else:
            index = self.model.index(0, 0, parent)

        self.popup.setCurrentIndex(index)

        margin = self.popup.frameWidth() * 2
        height = margin
        parent = self.popup.rootIndex()
        for row in range(min(10, self.model.rowCount(parent))):
            height += self.popup.sizeHintForRow(row)
        width = max(self.popup.sizeHint().width(), self.width())
        self.popup.resize(width, height)

    def currentIndex(self):
        return self._currentIndex

    def setCurrentIndex(self, index):
        if (
            index.isValid()
            and index.model() != self.model
            or self._currentIndex == index
        ):
            return
        self._currentIndex = index
        self.popup.hide()
        self.setText(
            index.data() if index.isValid() else self._placeholderText)
        self._emitIndexChanged(index)

    def itemClicked(self, index):
        if self.model.hasChildren(index):
            print(f'itremClicked({self.model.data(index)}): has children')
            self.setPopupRoot(index)
        elif isinstance(index.data(Qt.ItemDataRole.UserRole), bool):
            print(f'itremClicked({self.model.data(index)}): userRole: {index.data(Qt.ItemDataRole.UserRole)}')
            self.setPopupRoot(index.parent().parent())
        elif self.model.flags(index) & Qt.ItemFlag.ItemIsEnabled:
            print(f'itremClicked({self.model.data(index)}): popping up')
            self._currentIndex = index
            self.popup.hide()
            self.setText(index.data())
            self._emitIndexChanged(index)
        else:
            print(f'itremClicked({self.model.data(index)}): is disabled: ignoring')


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QTreeView, QFrame, QVBoxLayout, QComboBox

    import Pers
    import Vocations

    app = QApplication(sys.argv)

    if True:
        m = Pers.ThingsModel()
        f = Pers.ThingsFilter()
        f.setSourceModel(m)
        d = QFrame()
        l = QVBoxLayout()
        c = QComboBox()
        c.setModel(m)
        l.addWidget(c)
        v = QComboBox()
        v.setModel(Vocations.VocationsModel())
        v.currentTextChanged.connect(lambda x: f.set_vocation(x))
        l.addWidget(v)
        w = QTreeView()
        w.setModel(f)
        l.addWidget(w)
        r = RecursiveCombo()
        r.setModel(f)
        r.indexChanged[str].connect(lambda t: print(f'indexChanged({t})'))
        l.addWidget(r)
        d.setLayout(l)
        d.show()
        app.exec()
        d.hide()
        sys.exit(0)
