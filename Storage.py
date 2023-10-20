from collections import namedtuple
from typing import Optional

from PyQt6 import uic
from PyQt6.QtCore import QAbstractTableModel, pyqtSlot, Qt, QSortFilterProxyModel
from PyQt6.QtWidgets import QWidget, QTableView, QHeaderView, QButtonGroup, QPushButton

import Fandom
from DDDAfile import DDDAfile


class IModel(QAbstractTableModel):
    _column = namedtuple('_column', "name func hint align")

    def __init__(self, columns: [_column]):
        self._columns = columns
        super().__init__()
        self._rows = []
        self.select()

    def data(self, index, role=...):
        match role:
            case Qt.ItemDataRole.DisplayRole:
                try:
                    row = self._rows[index.row()]
                    return self._columns[index.column()].func(row)
                except KeyError:
                    print(f'ERROR: inknown item  in row {row}')
                    return '*** UNKNOWN ***'
            case Qt.ItemDataRole.TextAlignmentRole:
                return self._columns[index.column()].align
        return None

    def headerData(self, section, orientation, role=...):
        if orientation == Qt.Orientation.Horizontal:
            match role:
                case Qt.ItemDataRole.DisplayRole:
                    return self._columns[section].name
        return None

    def rowCount(self, parent=...):
        return len(self._rows)

    def columnCount(self, parent=...):
        return len(self._columns)

    def select(self, what=None):
        self.beginResetModel()
        self._rows = []
        self.endResetModel()

    def set_hints(self, view: QTableView):
        header = view.horizontalHeader()
        for i, x in enumerate(self._columns):
            header.setSectionResizeMode(i, x.hint)


class ItemModel(IModel):
    def __init__(self):
        super().__init__([
            IModel._column('ID', lambda x: x['ID'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            IModel._column('Name', lambda x: x['Name'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            IModel._column('Description', lambda x: x['desc'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
        ])

    def select(self, what='ALL'):
        self.beginResetModel()
        items = []
        for x in Fandom.all_by_name.values():
            if what == 'ALL' or x['Type'] == what:
                items.append(x)
        self._rows = items
        self.endResetModel()

    def id(self, idx: int):
        return self._rows[idx]['ID']

    def value(self, idx: int):
        return self._rows[idx]


class StorageModel(IModel):
    def __init__(self):
        super().__init__([
            IModel._column('ID', lambda x: x['ID'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            IModel._column('Item', lambda x: Fandom.all_by_id[x['ID']]['Name'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            IModel._column('Type', lambda x: Fandom.all_by_id[x['ID']]['Type'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            IModel._column('Count', lambda x: x['count'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
        ])

    def select(self, what=None):
        self.beginResetModel()
        items = [{'ID': 47, 'count': 1},
                 {'ID': 470, 'count': 2},
                 {'ID': 773, 'count': 3},
                 {'ID': 812, 'count': 4},
                 ]
        self._rows = items
        self.endResetModel()

    def edit(self, idx: int, add: int):
        self.beginResetModel()
        for x in self._rows:
            if x['ID'] == idx:
                x['count'] += add
                break
        else:
            x = {'ID': idx, 'count': add}
            self._rows.append(x)
        if x['count'] <= 0:
            self._rows.remove(x)
        self.endResetModel()


class DDDAModel(StorageModel):
    def __init__(self, ddda: DDDAfile):
        self.ddda = ddda
        super().__init__()

    def select(self, what=None):
        self.beginResetModel()
        store = self.ddda.store()
        self._rows = store
        self.endResetModel()


class Storage(QWidget):
    def __init__(self, ddda=None, *args, **kwargs):
        self.items: Optional[QTableView] = None
        self.storage: Optional[QTableView] = None
        super().__init__(*args, **kwargs)
        uic.loadUi("Storage.ui", self)
        self.item_model = ItemModel()
        self.item_proxy = QSortFilterProxyModel()
        self.item_proxy.setSourceModel(self.item_model)
        self.items.setModel(self.item_proxy)
        self.item_model.set_hints(self.items)
        self.items.setSortingEnabled(True)
        self.items.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.items.reset()

        self.b_group = QButtonGroup(self)
        for n, x in self.__dict__.items():
            if n.startswith('b_') and isinstance(x, QPushButton):
                # print(n)
                self.b_group.addButton(x)

        self.b_group.buttonClicked.connect(lambda b: self.item_model.select(b.text()))

        if ddda is not None:
            self.storage_model = DDDAModel(ddda)
        else:
            self.storage_model = StorageModel()
        self.storage.setModel(self.storage_model)
        self.storage_model.set_hints(self.storage)

    @pyqtSlot()
    def on_add_clicked(self):
        sel = self.items.currentIndex()
        if sel.isValid():
            orig = self.item_proxy.mapToSource(sel)
            idx = self.item_model.id(orig.row())
            self.storage_model.edit(idx, 1)

    @pyqtSlot()
    def on_del_clicked(self):
        sel = self.items.currentIndex()
        if sel.isValid():
            orig = self.item_proxy.mapToSource(sel)
            idx = self.item_model.id(orig.row())
            self.storage_model.edit(idx, -1)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QMainWindow, QApplication

    class MainWindow(QMainWindow):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setWindowTitle('Storage')
            self.ddda_file = DDDAfile()
            self.ddda_file.fname = '../DDsavetool/DDDA.sav'
            self.storage = Storage(ddda=self.ddda_file)
            self.setCentralWidget(self.storage)
            self.resize(1200, 1000)


    app = QApplication([])
    win = MainWindow()
    win.show()

    from sys import exit
    exit(app.exec())
