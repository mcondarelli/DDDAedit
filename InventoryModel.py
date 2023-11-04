from PyQt6.QtCore import Qt, pyqtSlot, QSortFilterProxyModel, QModelIndex

from AbstractModel import AbstractModel, DelegateBase
from DDDAwrapper import Tier, PersonWrapper as PW
from Fandom import all_by_id


class InventoryModel(AbstractModel):
    def __init__(self):
        super().__init__([
            AbstractModel.Column('ID', self.get_id),
            AbstractModel.Column('Item', self.get_item,
                                 align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            AbstractModel.Column('Type', self.get_type,
                                 align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            AbstractModel.Column('Count', self.get_count),
            AbstractModel.Column('Flag', self.get_flag,
                                 align=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
        ])
        self._inventory = None

    def select(self, what=None):
        if self._inventory:
            self._inventory.changed.disconnect(self.changed)
            self._inventory.rowchanged.disconnect(self.rowchanged)

        self._inventory = what
        self._inventory.changed.connect(self.changed)
        self._inventory.rowchanged.connect(self.rowchanged)
        self.changed()

    def setData(self, index, value, role = ...):
        column = index.column()
        if role == Qt.ItemDataRole.EditRole:
            if func := self._columns[column] is not None:
                func(index, value)

    def get_id(self, x):
        return str(PW.row_item(x))

    def get_item(self, x):
        return all_by_id[PW.row_item(x)]['Name']

    def get_type(self, x):
        return all_by_id[PW.row_item(x)]['Type']

    def is_armor(self, x):
        item = PW.row_item(x)
        item_type = all_by_id[item]['Type']
        return item_type in [
            'Arms Armor',
            'Chest Clothing',
            'Cloak',
            'Head Armor',
            'Leg Armor',
            'Leg Clothing',
            'Torso Armor',
        ]

    def is_weapon(self, x):
        item = PW.row_item(x)
        item_type = all_by_id[item]['Type']
        return item_type in [
            'Archistaves',
            'Daggers',
            'Longbows',
            'Longswords',
            'Maces',
            'Magick Bows',
            'Magick Shields',
            'Shields',
            'Shortbows',
            'Staves',
            'Swords',
            'Warhammers',
        ]

    def is_equipment(self, x):
        if isinstance(x, QModelIndex):
            x = self._inventory.rows[x.row()]
        return self.is_armor(x) or self.is_weapon(x)

    def get_flag(self, x):
        level = PW.row_flag(x)
        if self.is_equipment(x):
            return Tier.by_id[level]
        return level

    def set_flag(self, x, value):
        if isinstance(x, QModelIndex):
            x = self._inventory.rows[x.row()]
        if isinstance(value, str):
            value = Tier.by_tag[value]
        PW.row_set_flag(x, value)

    def get_count(self, x):
        return str(PW.row_num(x))

    @pyqtSlot()
    def changed(self):
        self.beginResetModel()
        self._rows = self._inventory.rows
        self.endResetModel()

    @pyqtSlot(int)
    def rowchanged(self, index):
        self.dataChanged.emit(
            self.index(index, 0), self.index(index, len(self._columns) - 1))


class InventoryProxy(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        row = self.sourceModel().row(source_row)
        return PW.row_valid(row)


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget, QComboBox
    from Storage import Storage
    from DDDAwrapper import DDDAwrapper, PersonWrapper

    app = QApplication(sys.argv)
    mw = Storage()
    wr = DDDAwrapper()
    wr.from_file('/tmp/t/DDDA.sav')
    # p0 = PersonWrapper(wr, 'Player')
    mw.set_storage_model(wr)
    # pw = InventoryModel()
    # pw.select(p0)
    # mw.storage_model = pw
    # mw.storage_proxy = InventoryProxy()
    # mw.storage_proxy.setSourceModel(mw.storage_model)
    # mw.storage.setModel(mw.storage_proxy)
    # mw.storage_model.set_hints(mw.storage)
    # mw.storage.setSortingEnabled(True)
    # mw.storage.sortByColumn(2, Qt.SortOrder.AscendingOrder)
    # self.storage.selectionModel().currentRowChanged.connect(self.on_storage_selection_changed)

    mw.resize(1200, 1000)
    mw.show()
    sys.exit(app.exec())
