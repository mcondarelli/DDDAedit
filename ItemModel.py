from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtWidgets import QHeaderView

import Fandom
from AbstractModel import AbstractModel


class ItemModel(AbstractModel):
    def __init__(self):
        self.what = 'ALL'
        super().__init__([
            AbstractModel._column('ID', lambda x: x['ID'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            AbstractModel._column('Name', lambda x: x['Name'],
                           QHeaderView.ResizeMode.ResizeToContents,
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            AbstractModel._column('Description', lambda x: x['desc'],
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

