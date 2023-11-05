from os import path
from typing import Optional

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QComboBox

import DDDAwrapper
import Fandom
import ItemModel
import Vocations


class Equipment(QWidget):
    def __init__(self, parent=None):
        self.person_wrapper: Optional[DDDAwrapper.PersonWrapper] = None

        def setmodel(wid, typ):
            m = ItemModel.ItemModel()  # SplitItemModel.SplitItemModel(typ)
            p = ItemModel.ItemProxy()  # SplitItemModel.SplitItemProxy()
            p.setSourceModel(m)
            p.set_type(typ)
            self.vocation.currentTextChanged.connect(p.set_vocation)
            wid.setModel(p)
            wid.setModelColumn(1)
            wid.setCurrentIndex(-1)
            wid.currentTextChanged.connect(lambda s: print(f'Equipment({typ}): Changed to "{s}"'))

        super().__init__(parent)
        self.head: Optional[QComboBox] = None
        self.torso: Optional[QComboBox] = None
        self.chest: Optional[QComboBox] = None
        self.pants: Optional[QComboBox] = None
        self.boots: Optional[QComboBox] = None
        self.arms: Optional[QComboBox] = None
        self.jewel1: Optional[QComboBox] = None
        self.primary: Optional[QComboBox] = None
        self.cape: Optional[QComboBox] = None
        self.jewel2: Optional[QComboBox] = None
        self.secondary: Optional[QComboBox] = None

        self.sex: Optional[QComboBox] = None
        self.vocation: Optional[QComboBox] = None

        here = path.dirname(path.realpath('__file__'))
        uic.loadUi(path.join(here, "Equipment.ui"), self)

        setmodel(self.head, 'Head Armor')
        setmodel(self.torso, 'Torso Armor')
        setmodel(self.chest, 'Chest Clothing')
        setmodel(self.pants, 'Leg Clothing')
        setmodel(self.boots, 'Leg Armor')
        setmodel(self.arms, 'Arms Armor')
        setmodel(self.jewel1, 'Jewelry')
        setmodel(self.primary, 'ALL')
        setmodel(self.cape, 'Cloak')
        setmodel(self.jewel2, 'Jewelry')
        setmodel(self.secondary, 'ALL')

        self.vocation.clear()
        # self.vocation.addItems(_vocations.keys())
        self.vocation.addItems(Vocations.vocations())

    def set_equipment(self, person_wrapper):
        self.person_wrapper = person_wrapper
        vocation = self.person_wrapper.vocation
        self.vocation.setCurrentText(Vocations.name(vocation))

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


if __name__ == '__main__':
    from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget


    class MainWindow(QMainWindow):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setWindowTitle('Equipment')
            self.equipment = Equipment()
            self.setCentralWidget(self.equipment)

    app = QApplication([])
    win = MainWindow()
    win.show()

    from sys import exit
    exit(app.exec())
