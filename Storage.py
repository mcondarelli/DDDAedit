from os import path
from typing import Optional

from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot, Qt, QModelIndex
from PyQt6.QtGui import QStatusTipEvent
from PyQt6.QtWidgets import QWidget, QTableView, QButtonGroup, QPushButton, QLineEdit, QLabel, \
    QComboBox, QApplication

import AbstractModel
from DDDAwrapper import DDDAwrapper, PersonWrapper, Tier
from InventoryModel import InventoryProxy, InventoryModel
from ItemModel import ItemModel, ItemProxy


class TierEditDelegate(AbstractModel.DelegateBase):
    def createEditor(self, parent, option, index):
        combobox = QComboBox(parent)
        for i, tag in enumerate(Tier.all_tags()):
            combobox.insertItem(i, tag)
            combobox.setItemData(i, Tier(tag).idx(), Qt.ItemDataRole.UserRole)
        combobox.activated.connect(lambda value: self.commitData.emit(combobox))
        return combobox

    # def paint(self, painter, option, index):
    #     data = index.data(Qt.ItemDataRole.UserRole)
    #     print(data)
    #     # if isinstance(data, int):
    #     #     ptr = index.internalPointer()
    #     #     ptr.setData(Tier.by_id[data], Qt.ItemDataRole.DisplayRole)
    #     super().paint(painter, option, index)

    def can_edit(self, index: QModelIndex):
        # return index.model().is_equipment(index.model()._inventory.rows[index.row()])
        return index.model().is_equipment(index)

    def setModelData(self, editor, model, index):
        value = editor.currentData(Qt.ItemDataRole.UserRole)
        if isinstance(model, InventoryProxy):
            index = model.mapToSource(index)
            model = model.sourceModel()
        model.set_flag(index, value)


class Storage(QWidget):
    def __init__(self, ddda=None, *args, **kwargs):
        self.tier_delegate = None
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
        self.tier_delegate = TierEditDelegate(self.storage)
        self.storage_model.set_delegate(4, self.tier_delegate)
        self.storage.setItemDelegateForColumn(4, self.tier_delegate)
        self.items.selectionModel().currentRowChanged.connect(self.on_items_selection_changed)

    @pyqtSlot()
    def on_add_clicked(self):
        sel = self.items.currentIndex()
        if sel.isValid():
            orig = self.item_proxy.mapToSource(sel)
            idx = self.item_model.id(orig.row())
            if self.person_wrapper is not None:
                self.person_wrapper.add(idx)
            else:
                QApplication.sendEvent(self, QStatusTipEvent('Select a Person to add thing to'))

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
        if sm := self.storage.selectionModel() is not None:
            sm.clearSelection()

    @pyqtSlot(str)
    def on_owner_currentTextChanged(self, text):
        self.person_wrapper = self.storage_wrapper.person(text)
        self.storage_model.select(self.person_wrapper)
        self.storage_proxy.setSourceModel(self.storage_model)
        self.storage.setModel(self.storage_proxy)
        self.storage_model.set_hints(self.storage)
        self.storage.setSortingEnabled(True)
        self.storage.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        self.owner_name.setText(self.person_wrapper.name)
        QApplication.sendEvent(self, QStatusTipEvent(''))


if __name__ == '__main__':
    test_storage = True
    from PyQt6.QtWidgets import (QMainWindow, QTableWidget, QTableWidgetItem)
    from DDDAwrapper import DDDAwrapper

    class MainWindow(QMainWindow):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if test_storage:
                self.setWindowTitle('Storage')
                self.storage = Storage()
                self.setCentralWidget(self.storage)
                self.resize(1200, 1000)
                self.wrapper = DDDAwrapper()
                self.wrapper.from_file('/tmp/t/DDDA.sav')
                self.storage.set_storage_model(self.wrapper)
                self.setWindowTitle("Storage test")
            else:
                lst = [("Alice", "1 star"),
                       ("Neptun", "1 star"),
                       ("Ferdinand", "1 star")]
                table = QTableWidget(3, 2)
                table.setHorizontalHeaderLabels(["Name", "Tier"])
                table.verticalHeader().setVisible(False)
                table.resize(150, 50)

                for i, (nam, tier) in enumerate(lst):
                    nameItem = QTableWidgetItem(nam)
                    tierItem = QTableWidgetItem()
                    tierItem.setData(Qt.ItemDataRole.DisplayRole, tier)
                    table.setItem(i, 0, nameItem)
                    table.setItem(i, 1, tierItem)

                table.resizeColumnToContents(0)
                table.horizontalHeader().setStretchLastSection(True)
                table.setItemDelegateForColumn(1, TierEditDelegate(table))
                self.table = table

                self.setCentralWidget(self.table)

                self.setWindowTitle("Color Editor Factory")

        def closeEvent(self, _):
            if not test_storage:
                for r in range(self.table.rowCount()):
                    print(f'| {self.table.item(r, 0).text():^20s} | {Tier(self.table.item(r, 1).text()).idx():4d} |')


    app = QApplication([])
    win = MainWindow()
    win.show()

    from sys import exit
    exit(app.exec())
