from PyQt6.QtCore import QAbstractListModel, Qt, pyqtProperty, pyqtSignal, QSortFilterProxyModel

import Fandom

_vocations = [
    'Fighter', 'Strider', 'Mage',
    'Assassin', 'Magick Archer', 'Mystic Knight',
    'Warrior', 'Ranger', 'Sorcerer'
]


class SplitItemModel(QAbstractListModel):
    available = '**index**'
    selected_changed = pyqtSignal(str)

    _data = {'ALL': []}
    for item in Fandom.all_by_id.values():
        typ = item['Type']
        if typ not in _data:
            _data[typ] = []
        _data[typ].append(item)
        _data['ALL'].append(item)

    def __init__(self, who: str = 'ALL', parent=None):
        super().__init__(parent)
        self._selected = who

    def rowCount(self, parent=...):
        if self._selected == SplitItemModel.available:
            return len(self._data)
        return len(self._data[self._selected])

    def data(self, index, role=...):
        if self._selected == SplitItemModel.available:
            if role == Qt.ItemDataRole.DisplayRole:
                a = []
                a.extend(self._data.keys())
                return a[index.row()]
        else:
            match role:
                case Qt.ItemDataRole.DisplayRole:
                    return self._data[self._selected][index.row()]['Name']
                case Qt.ItemDataRole.ToolTipRole:
                    return self._data[self._selected][index.row()]['desc']

    def headerData(self, section, orientation, role=...):
        if self._selected == SplitItemModel.available:
            return SplitItemModel.available
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._selected

    def selectables(self):
        return self._data.keys()

    @pyqtProperty(str)
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, who:str):
        self.beginResetModel()
        self._selected = who
        self.endResetModel()
        self.selected_changed.emit(who)

    def row(self, r: int) -> dict:
        return self._data[self._selected][r]


class SplitItemProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._vocation = ''

    def vocation(self):
        return self._vocation

    def set_vocation(self, voc):
        if not voc or voc in _vocations:
            self.beginResetModel()
            self._vocation = voc
            self.endResetModel()

    def filterAcceptsRow(self, source_row, source_parent):
        row = self.sourceModel().row(source_row)
        try:
            return row['usable'][self._vocation]
        except:
            return True


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox

    model = SplitItemModel()
    proxy = SplitItemProxy()
    proxy.setSourceModel(model)

    def on_wh_currentTextChanged(who):
        model.selected = who

    app = QApplication(sys.argv)
    mw = QWidget()
    lo = QVBoxLayout()
    wh = QComboBox()
    # wh.addItems(model.selectables())
    wh.setModel(SplitItemModel(SplitItemModel.available))
    wh.currentTextChanged.connect(on_wh_currentTextChanged)
    lo.addWidget(wh)
    it = QComboBox()
    it.setModel(proxy)
    lo.addWidget(it)
    vo = QComboBox()
    vo.addItems(_vocations)
    vo.setCurrentIndex(-1)
    vo.setPlaceholderText('ALL')
    vo.currentTextChanged.connect(lambda x: proxy.set_vocation(x))
    lo.addWidget(vo)
    mw.setLayout(lo)

    mw.show()
    sys.exit(app.exec())
