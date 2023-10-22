from collections import namedtuple

from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtWidgets import QTableView


class AbstractModel(QAbstractTableModel):
    _column = namedtuple('_column', "name func hint align")

    def __init__(self, columns: [_column]):
        self._columns = columns
        super().__init__()
        self._rows = []
        # self.select()

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

    def row(self, idx: int):
        return self._rows[idx]
