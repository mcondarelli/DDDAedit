from typing import Optional

from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt, pyqtSlot
import DDDAwrapper
import InventoryModel
import picwidgets

import Vocations
from Equipment import Equipment


class Pers(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.person_wrapper: Optional[DDDAwrapper.PersonWrapper] = None

        self.name: Optional[QtWidgets.QLineEdit] = None
        self.level: Optional[QtWidgets.QSpinBox] = None
        self.vo: Optional[picwidgets.PicGrid] = None
        self.se: Optional[picwidgets.StarEditor] = None
        self.inventory: Optional[QtWidgets.QTableView] = None
        self.equipment: Optional[Equipment] = None
        uic.loadUi("Pers.ui", self)

        self.vo.set_data(
            [[Vocations.icon(1), Vocations.icon(2), Vocations.icon(3)],
             [Vocations.icon(4), Vocations.icon(5), Vocations.icon(6)],
             [Vocations.icon(7), Vocations.icon(8), Vocations.icon(9)]
             ])
        self.vo.selec.connect(self.on_vocation_selec)
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
            self.equipment.set_equipment(self.person_wrapper)
        else:
            self.setEnabled(False)

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
    from PyQt6.QtWidgets import QApplication  # , QTreeView, QFrame, QVBoxLayout

    app = QApplication(sys.argv)

    mw = Pers()
    wr = DDDAwrapper.DDDAwrapper()
    wr.from_file('/tmp/t/DDDA.sav')
    p0 = DDDAwrapper.PersonWrapper(wr, 'Player')
    mw.set_data(p0)

    mw.show()
    sys.exit(app.exec())
