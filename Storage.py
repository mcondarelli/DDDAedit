from collections import namedtuple
from os import path
from typing import Optional

from PyQt6 import uic
from PyQt6.QtCore import QAbstractTableModel, pyqtSlot, Qt, QSortFilterProxyModel, QModelIndex, \
    QItemSelectionModel
from PyQt6.QtWidgets import QWidget, QTableView, QHeaderView, QButtonGroup, QPushButton, QLineEdit, QLabel

import Fandom
from DDDAwrapper import DDDAwrapper, PersonWrapper
from InventoryModel import InventoryProxy, InventoryModel


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


class Storage(QWidget):
    def __init__(self, ddda=None, *args, **kwargs):
        self.items: Optional[QTableView] = None
        self.storage: Optional[QTableView] = None
        self.filter: Optional[QLineEdit] = None
        self.owner_name: Optional[QLabel] = None
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

        self.storage_wrapper: Optional[DDDAwrapper] = None
        self.person_wrapper: Optional[PersonWrapper] = None
        self.storage_model: Optional[InventoryModel] = None
        self.storage_proxy: Optional[InventoryProxy] = None

    def set_storage_model(self, wrapper: DDDAwrapper):
        self.storage_wrapper = wrapper
        self.storage_model = InventoryModel()
        self.storage_proxy = InventoryProxy()
        self.items.selectionModel().currentRowChanged.connect(self.on_items_selection_changed)


    @pyqtSlot()
    def on_add_clicked(self):
        sel = self.items.currentIndex()
        if sel.isValid():
            orig = self.item_proxy.mapToSource(sel)
            idx = self.item_model.id(orig.row())
            self.person_wrapper.add(idx)

    def _inc(self, val):
        sel = self.storage.currentIndex()
        if sel.isValid():
            orig = self.storage_proxy.mapToSource(sel)
            row = self.storage_model.row(orig.row())
            self.person_wrapper.row_inc(row, val)

    @pyqtSlot()
    def on_inc_clicked(self):
        self._inc(1)

    @pyqtSlot()
    def on_dec_clicked(self):
        self._inc(-1)

    @pyqtSlot(str)
    def on_filter_textChanged(self, text):
        self.item_proxy.set_filter(text)

    @pyqtSlot(QModelIndex, QModelIndex)
    def on_storage_selection_changed(self, _new: QModelIndex, _old):
        self.items.clearSelection()

    @pyqtSlot(QModelIndex, QModelIndex)
    def on_items_selection_changed(self, _new: QModelIndex, _old):
        self.storage.selectionModel().clearSelection()

    @pyqtSlot(str)
    def on_owner_currentTextChanged(self, text):
        self.person_wrapper = PersonWrapper(self.storage_wrapper, text)
        self.storage_model.select(self.person_wrapper)
        self.storage_proxy.setSourceModel(self.storage_model)
        self.storage.setModel(self.storage_proxy)
        self.storage_model.set_hints(self.storage)
        self.storage.setSortingEnabled(True)
        self.storage.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        self.owner_name.setText(self.person_wrapper.name)


# if __name__ == '__main__':
#     from PyQt6.QtWidgets import QMainWindow, QApplication
#
#     class MainWindow(QMainWindow):
#         def __init__(self, *args, **kwargs):
#             super().__init__(*args, **kwargs)
#             self.setWindowTitle('Storage')
#             self.storage = Storage()
#             self.setCentralWidget(self.storage)
#             self.resize(1200, 1000)
#             self.ddda_file = DDDAfile()
#             self.ddda_file.fname = '../DDsavetool/DDDA.sav'
#             self.storage.set_storage_model(self.ddda_file)
#
#
#     app = QApplication([])
#     win = MainWindow()
#     win.show()
#
#     from sys import exit
#     exit(app.exec())
