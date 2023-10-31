from typing import Optional

from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt, pyqtSlot, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QComboBox

import DDDAwrapper
import Fandom
import InventoryModel
import picwidgets

import Vocations

weapons = {'primary': ['Archistaves', 'Daggers', 'Longswords', 'Maces', 'Staves', 'Swords', 'Warhammers'],
           'secondary': ['Longbows', 'Magick Bows', 'Magick Shields', 'Shields', 'Shortbows']}


class ThingsModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.types = {}
        root = self.invisibleRootItem()
        for i in Fandom.all_by_id.values():
            if i['Type'] not in self.types:
                typ = QStandardItem(i['Type'])
                root.appendRow(typ)
                self.types[i['Type']] = typ
            t = self.types[i['Type']]
            item = QStandardItem(i['Name'])
            item.setData(i, Qt.ItemDataRole.UserRole)
            t.appendRow(item)


class ThingsFilter(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self._vocation = ''
        self._weapon = ''
        self._type = ''

    def vocation(self):
        return self._vocation

    def set_vocation(self, voc):
        if not voc or voc in Vocations.vocations():
            self.beginResetModel()
            self._vocation = voc
            self.endResetModel()

    def set_type(self, typ):
        # TODO: check it is an acceptable entry
        self.beginResetModel()
        self._type = typ
        self.endResetModel()

    def set_weapon(self, weapon):
        # TODO: check it is an acceptable entry
        self.beginResetModel()
        self._weapon = weapon
        self.endResetModel()

    def _weapons(self):
        if self._vocation:
            match self._weapon:
                case 'primary':
                    return Vocations.primary(self._vocation)
                case 'secondary':
                    return Vocations.secondary(self._vocation)
                case 'ALL':
                    return Vocations.primary(self._vocation) + Vocations.secondary(self._vocation)
                case _:
                    return []
        else:
            return []

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        ddata = self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole)

        if self._type and self.sourceModel().itemFromIndex(index).parent() is None:  # top level items
            if self._type != ddata:
                return False

        if self._weapon and source_parent.parent() is None:  # top level items
            if ddata not in self._weapons():
                return False

        udata = self.sourceModel().data(index, Qt.ItemDataRole.UserRole)
        try:
            return udata['usable'][self._vocation]
        except (KeyError, TypeError):
            return True

    def root_index(self, name: str = None):
        name = name or self._type
        for n in range(self.rowCount()):
            index = self.index(n, 0)
            k = self.data(index)
            if k == name:
                return index
        return None


class Pers(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.person_wrapper: Optional[DDDAwrapper.PersonWrapper] = None
        # self.item_data: Optional[DDDAwrapper.PersonWrapper] = None

        self.name: Optional[QtWidgets.QLineEdit] = None
        self.level: Optional[QtWidgets.QSpinBox] = None
        self.vo: Optional[picwidgets.PicGrid] = None
        self.se: Optional[picwidgets.StarEditor] = None
        self.inventory: Optional[QtWidgets.QTableView] = None
        uic.loadUi("Pers.ui", self)

        self.vo.set_data(
            [[Vocations.icon(1), Vocations.icon(2), Vocations.icon(3)],
             [Vocations.icon(4), Vocations.icon(5), Vocations.icon(6)],
             [Vocations.icon(7), Vocations.icon(8), Vocations.icon(9)]
             ])
        self.vo.selec.connect(self.on_vocation_selec)
        # self.se.set_stars(9, 1)
        self.se.editing_finished.connect(self.on_vocation_level)

        self.storage_wrapper: Optional[DDDAwrapper] = None
        self.person_wrapper: Optional[DDDAwrapper.PersonWrapper] = None
        self.inventory_model: Optional[InventoryModel.InventoryModel] = None
        self.inventory_proxy: Optional[InventoryModel.InventoryProxy] = None

        m = ThingsModel()

        def setup_combo(cb: QComboBox, m: ThingsModel, typ: str):
            f = ThingsFilter()
            f.setSourceModel(m)
            f.set_type(typ)
            cb.setModel(f)
            cb.setRootModelIndex(f.root_index())

        setup_combo(self.arms, m, 'Arms Armor')
        setup_combo(self.boots, m, 'Leg Armor')
        setup_combo(self.cape, m, 'Cloak')
        setup_combo(self.chest, m, 'Chest Clothing')
        setup_combo(self.head, m, 'Head Armor')
        setup_combo(self.jewel1, m, 'Jewelry')
        setup_combo(self.jewel2, m, 'Jewelry')
        setup_combo(self.pants, m, 'Leg Clothing')
        setup_combo(self.torso, m, 'Torso Armor')

    def set_data(self, data: DDDAwrapper.PersonWrapper):
        self.person_wrapper = data
        pers = data.person
        if pers:
            self.setEnabled(True)
            self.name.setText(self.person_wrapper.name)
            self.level.setValue(self.person_wrapper.level)
            self.vo.select(self.person_wrapper.vocation)
            self.se.set_stars(self.person_wrapper.vocation_level)

            self.inventory_model = InventoryModel.InventoryModel()
            self.inventory_proxy = InventoryModel.InventoryProxy()
            self.inventory_model.select(self.person_wrapper)
            self.inventory_proxy.setSourceModel(self.inventory_model)
            self.inventory.setModel(self.inventory_proxy)
            self.inventory_model.set_hints(self.inventory)
            self.inventory.setSortingEnabled(True)
            self.inventory.sortByColumn(2, Qt.SortOrder.AscendingOrder)
            self._set_armor()
        else:
            self.setEnabled(False)

    def _set_armor(self):
        def set_equipment(tag: str, what: int, where: QComboBox):
            if what < 0:
                print(f'{tag}: UNEQUIPPED ({what})')
                where.setCurrentIndex(-1)
            else:
                name = Fandom.all_by_id[what]['Name']
                print(f'{tag}: {name} ({what})')
                where.setCurrentText(name)

        set_equipment('Primary Weapon', self.person_wrapper.equipment.primary.idx, self.primary)
        set_equipment('Secondary Weapon', self.person_wrapper.equipment.secondary.idx, self.secondary)
        set_equipment('Clothing (shirt)', self.person_wrapper.equipment.shirt.idx, self.chest)
        set_equipment('Clothing (pants)', self.person_wrapper.equipment.pants.idx, self.pants)
        set_equipment('Helmet', self.person_wrapper.equipment.helmet.idx, self.head)
        set_equipment('Chestplate', self.person_wrapper.equipment.chest.idx, self.torso)
        set_equipment('Gauntlets', self.person_wrapper.equipment.gauntlets.idx, self.arms)
        set_equipment('Greaves', self.person_wrapper.equipment.greaves.idx, self.boots)
        set_equipment('Cape', self.person_wrapper.equipment.cape.idx, self.cape)
        set_equipment('Jewel 1', self.person_wrapper.equipment.jewel1.idx, self.jewel1)
        set_equipment('Jewel 2', self.person_wrapper.equipment.jewel2.idx, self.jewel2)

    @pyqtSlot(int)
    def on_level_valueChanged(self, value: int):
        self.person_wrapper.level = value

    @pyqtSlot(object)
    def on_vocation_selec(self, param):
        self.person_wrapper.vocation = param

    @pyqtSlot(int)
    def on_vocation_level(self, level):
        self.person_wrapper.vocation_level = level

    def _inc(self, val):
        sel = self.inventory.currentIndex()
        if sel.isValid():
            orig = self.inventory_proxy.mapToSource(sel)
            row = self.inventory_model.row(orig.row())
            self.person_wrapper.row_inc(row, val)

    @pyqtSlot()
    def on_inc_clicked(self):
        self._inc(1)

    @pyqtSlot()
    def on_dec_clicked(self):
        self._inc(-1)


if __name__ == '__main__':
    test = False
    import sys
    from PyQt6.QtWidgets import QApplication, QTreeView, QFrame, QVBoxLayout

    app = QApplication(sys.argv)

    if test:
        m = ThingsModel()
        f = ThingsFilter()
        f.setSourceModel(m)
        d = QFrame()
        l = QVBoxLayout()

        t = QComboBox()
        t.setModel(m)
        t.setCurrentIndex(-1)
        t.currentTextChanged.connect(lambda x: f.set_type(x))
        l.addWidget(t)

        a = QComboBox()
        a.addItems(['primary', 'secondary', 'ALL', 'None'])
        a.setCurrentIndex(-1)
        a.currentTextChanged.connect(f.set_weapon)
        l.addWidget(a)

        v = QComboBox()
        v.setModel(Vocations.VocationsModel())
        v.setCurrentIndex(-1)
        v.currentTextChanged.connect(f.set_vocation)
        l.addWidget(v)

        w = QTreeView()
        w.setModel(f)
        l.addWidget(w)

        d.setLayout(l)
        d.show()
        app.exec()
        d.hide()
        sys.exit(0)

    mw = Pers()
    wr = DDDAwrapper.DDDAwrapper()
    wr.from_file('/tmp/t/DDDA.sav')
    p0 = DDDAwrapper.PersonWrapper(wr, 'Player')
    mw.set_data(p0)

    mw.show()
    sys.exit(app.exec())
