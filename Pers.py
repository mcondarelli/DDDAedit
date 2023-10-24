from typing import Optional

from PyQt6 import QtWidgets, QtCore, uic
from PyQt6.QtCore import Qt, pyqtSlot

import DDDAwrapper
import InventoryModel
import picwidgets


class Pers(QtWidgets.QWidget):
    vocs = [None,                                   # 0 invalid
            'resources/DDicon_fighter.webp',        # 1 Fighter
            'resources/DDicon_strider.webp',        # 2 Strider
            'resources/DDicon_mage.webp',           # 3 Mage
            'resources/DDicon_magicknight.webp',    # 4 Mystic Knight
            'resources/DDicon_assassin.webp',       # 5 Assassin
            'resources/DDicon_magicarcher.webp',    # 6 Magick Archer
            'resources/DDicon_warrior.webp',        # 7 Warrrior
            'resources/DDicon_ranger.webp',         # 8 Ranger
            'resources/DDicon_sorcerer.webp']       # 9 Sorcerer

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
            [[Pers.vocs[1], Pers.vocs[2], Pers.vocs[3]],
             [Pers.vocs[4], Pers.vocs[5], Pers.vocs[6]],
             [Pers.vocs[7], Pers.vocs[8], Pers.vocs[9]]
             ])
        self.vo.selec.connect(self.on_vocation_selec)
        # self.se.set_stars(9, 1)
        self.se.editing_finished.connect(self.on_vocation_level)

        self.storage_wrapper: Optional[DDDAwrapper] = None
        self.person_wrapper: Optional[DDDAwrapper.PersonWrapper] = None
        self.inventory_model: Optional[InventoryModel.InventoryModel] = None
        self.inventory_proxy: Optional[InventoryModel.InventoryProxy] = None

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
        print('Primary Weapon', self.person_wrapper.equipment.primary.idx)
        print('Secondary Weapon', self.person_wrapper.equipment.secondary.idx)
        print('Clothing (shirt)', self.person_wrapper.equipment.shirt.idx)
        print('Clothing (pants)', self.person_wrapper.equipment.pants.idx)
        print('Helmet', self.person_wrapper.equipment.helmet.idx)
        print('Chestplate', self.person_wrapper.equipment.chest.idx)
        print('Gauntlets', self.person_wrapper.equipment.gauntlets.idx)
        print('Greaves', self.person_wrapper.equipment.greaves.idx)
        print('Cape', self.person_wrapper.equipment.cape.idx)
        print('Jewel 1', self.person_wrapper.equipment.jewel1.idx)
        print('Jewel 2', self.person_wrapper.equipment.jewel2.idx)

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
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget

    app = QApplication(sys.argv)
    mw = Pers()
    wr = DDDAwrapper.DDDAwrapper()
    wr.from_file('/tmp/t/DDDA.sav')
    p0 = DDDAwrapper.PersonWrapper(wr, 'Player')
    mw.set_data(p0)

    mw.show()
    sys.exit(app.exec())
