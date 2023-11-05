from PyQt6.QtCore import Qt, QSortFilterProxyModel, QModelIndex
from PyQt6.QtWidgets import QHeaderView

import Fandom
from AbstractModel import AbstractModel


class ItemModel(AbstractModel):
    def __init__(self):
        self.what = 'ALL'
        super().__init__([
            AbstractModel.Column('ID', lambda x: x['ID'],
                                 QHeaderView.ResizeMode.ResizeToContents,
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            AbstractModel.Column('Name', lambda x: x['Name'],
                                 QHeaderView.ResizeMode.ResizeToContents,
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            AbstractModel.Column('Description', lambda x: x['desc'],
                                 QHeaderView.ResizeMode.ResizeToContents,
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
        ])
        self.select()

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

    def get_tooltip(self, index: QModelIndex):
        return self._rows[index.row()]['desc']


class ItemProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._type = 'ALL'
        self._head = ''
        self._vocation = ''

    def set_type(self, typ='ALL'):
        self._type = typ
        self.invalidateFilter()

    def set_filter(self, head=''):
        self._head = head.lower()
        self.invalidateFilter()

    def set_vocation(self, vocation: str):
        if vocation != self._vocation:
            self.beginResetModel()
            self._vocation = vocation
            self.endResetModel()

    def filterAcceptsRow(self, source_row, source_parent):
        mod: ItemModel = self.sourceModel()
        row = mod.value(source_row)
        if self._head and not row['Name'].lower().startswith(self._head):
            return False
        if self._type != 'ALL' and self._type != row['Type']:
            return False
        if self._vocation:
            usable = row.get('usable', None)
            if usable and not usable.get(self._vocation, True):
                return False
        return True
