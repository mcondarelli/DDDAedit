from collections import namedtuple
from os import path
from typing import Optional

from PyQt6 import uic
from PyQt6.QtCore import QAbstractTableModel, pyqtSlot, Qt, QSortFilterProxyModel, QModelIndex, \
    QItemSelectionModel
from PyQt6.QtWidgets import QWidget, QTableView, QHeaderView, QButtonGroup, QPushButton, QLineEdit

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
                    print(f'ERROR: unknown item  in row {row}')
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

    def select(self):
        self.beginResetModel()
        self._rows = []
        self.endResetModel()

    def set_hints(self, view: QTableView):
        header = view.horizontalHeader()
        for i, x in enumerate(self._columns):
            header.setSectionResizeMode(i, x.hint)


class ItemModel(IModel):
    def __init__(self):
        self.what = 'ALL'
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

    def select(self):
        self.beginResetModel()
        self._rows = [x for x in Fandom.all_by_name.values()]
        self.endResetModel()

    def id(self, idx: int):
        return self._rows[idx]['ID']

    def typ(self, idx: int):
        return self._rows[idx]['Type']

    def name(self, idx: int):
        return self._rows[idx]['Name']

    def value(self, idx: int):
        return self._rows[idx]


class ItemProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._type = 'ALL'
        self._head = ''

    def set_type(self, typ='ALL'):
        self._type = typ
        self.invalidateFilter()

    def set_filter(self, head=''):
        self._head = head.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        mod: ItemModel = self.sourceModel()
        row = mod.value(source_row)
        if self._head and not row['Name'].lower().startswith(self._head):
            return False
        if self._type != 'ALL' and self._type != row['Type']:
            return False
        return True


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
        self.ddda.storChanged.connect(self.select)

    def select(self, what=None):
        self.beginResetModel()
        store = self.ddda.store()
        self._rows = store
        self.endResetModel()

    def edit(self, idx: int, add: int):
        self.ddda.edit(idx, add)


class DDDAProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)


class Storage(QWidget):
    def __init__(self, ddda=None, *args, **kwargs):
        self.items: Optional[QTableView] = None
        self.storage: Optional[QTableView] = None
        self.filter: Optional[QLineEdit] = None
        super().__init__(*args, **kwargs)
        here = path.dirname(path.realpath('__file__'))
        uic.loadUi(path.join(here, "Storage.ui"), self)
        self.item_model = ItemModel()
        self.item_proxy = ItemProxy()
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
        self.b_group.buttonClicked.connect(lambda b: self.item_proxy.set_type(b.text()))

        self.storage_model: Optional[DDDAModel] = None
        self.storage_proxy: Optional[DDDAProxy] = None

    def set_storage_model(self, ddda: DDDAfile):
        self.storage_model = DDDAModel(ddda)
        self.storage_proxy = DDDAProxy()
        self.storage_proxy.setSourceModel(self.storage_model)
        self.storage.setModel(self.storage_proxy)
        self.storage_model.set_hints(self.storage)
        self.storage.setSortingEnabled(True)
        self.storage.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        self.storage.selectionModel().currentRowChanged.connect(self.on_storage_selection_changed)


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

    @pyqtSlot(str)
    def on_filter_textChanged(self, text):
        self.item_proxy.set_filter(text)

    @pyqtSlot(QModelIndex, QModelIndex)
    def on_storage_selection_changed(self, new: QModelIndex, _old):
        name = self.storage_proxy.data(new, Qt.ItemDataRole.DisplayRole)
        self.filter.setText(name)
        self.items.selectionModel().select(
            self.item_proxy.index(0, 0),
            QItemSelectionModel.SelectionFlag.SelectCurrent|QItemSelectionModel.SelectionFlag.Rows)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QMainWindow, QApplication

    class MainWindow(QMainWindow):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setWindowTitle('Storage')
            self.storage = Storage()
            self.setCentralWidget(self.storage)
            self.resize(1200, 1000)
            self.ddda_file = DDDAfile()
            self.ddda_file.fname = '../DDsavetool/DDDA.sav'
            self.storage.set_storage_model(self.ddda_file)


    app = QApplication([])
    win = MainWindow()
    win.show()

    from sys import exit
    exit(app.exec())
