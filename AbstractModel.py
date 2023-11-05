from dataclasses import dataclass
from typing import Callable, Any, Optional

from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt6.QtWidgets import QTableView, QHeaderView, QStyledItemDelegate


class DelegateBase(QStyledItemDelegate):
    def can_edit(self, index: QModelIndex):
        return True


class AbstractModel(QAbstractTableModel):
    @dataclass
    class Column:
        name: str
        func: Callable[[int], Any]
        hint: QHeaderView.ResizeMode = QHeaderView.ResizeMode.ResizeToContents
        align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        delegate: Optional[DelegateBase] = None

    def __init__(self, columns: [Column]):
        self._columns: [AbstractModel.Column] = columns
        super().__init__()
        self._rows = []

    def set_delegate(self, col: int, delegate: DelegateBase):
        self._columns[col].delegate = delegate

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
            case Qt.ItemDataRole.ToolTipRole:
                return self.get_tooltip(index)
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

    def row(self, idx: int):
        return self._rows[idx]

    def flags(self, index):
        flags = super().flags(index)
        if (delegate := self._columns[index.column()].delegate) is not None:
            if delegate.can_edit(index):
                flags |= Qt.ItemFlag.ItemIsEditable
            else:
                flags &= ~Qt.ItemFlag.ItemIsEditable
        return flags

    def get_tooltip(self, index: QModelIndex):
        return None
