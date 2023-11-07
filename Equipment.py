from os import path
from typing import Optional

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QComboBox, QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QCheckBox

from DDDAwrapper import Tier, PersonWrapper
import Fandom
import ItemModel
import Vocations


class EquipmentCombo(QComboBox):
    map_type = {
        'Primary Weapon': 'ALL',
        'Secondary Weapon': 'ALL',
        'Chest Clothing': 'Chest Clothing',
        'Leg Clothing': 'Leg Clothing',
        'Head Armor': 'Head Armor',
        'Torso Armor': 'Torso Armor',
        'Arms Armor': 'Arms Armor',
        'Leg Armor': 'Leg Armor',
        'Cloak': 'Cloak',
        'Jewelry 1': 'Jewelry',
        'Jewelry 2': 'Jewelry',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._person_wrapper = None
        self._slot = None

    def set_model(self, typ):
        self._slot = typ
        m = ItemModel.ItemModel()
        p = ItemModel.ItemProxy()
        p.setSourceModel(m)
        p.set_type(self.map_type[self._slot])
        self.setModel(p)
        self.setModelColumn(1)
        self.setCurrentIndex(-1)
        # wid.currentTextChanged.connect(lambda s: print(f'Equipment({typ}): Changed to "{s}"'))
        self.customContextMenuRequested.connect(lambda pos: self.show_menu(self, pos))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def set_equipment(self, wrapper: PersonWrapper, tag: str):
        self._person_wrapper = wrapper
        slot = self._person_wrapper.equipment[tag]
        what = slot.idx
        if what < 0:
            print(f'{tag}: UNEQUIPPED ({what})')
            self.setCurrentIndex(-1)
        else:
            name = Fandom.all_by_id[what]['Name']
            print(f'{tag}: {name} ({what})')
            self.setCurrentText(name)

    def show_menu(self, wid, pos):
        class Dialog(QDialog):
            def __init__(self, equipment, parent: EquipmentCombo):
                result = {}
                super().__init__(parent)
                self.setWindowTitle('Equipment details')
                self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                                  QDialogButtonBox.StandardButton.Cancel)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                self.layout = QVBoxLayout()
                desc = QLabel(equipment['desc'])
                desc.setStyleSheet('border: 2px solid goldenrod;')
                self.layout.addWidget(desc)
                flag = parent._person_wrapper.equipment[parent._slot].flag
                self.flag = flag.tag()
                self.kind = flag.kind
                self.layout.addWidget(QLabel(f'Flag kind is "{self.kind}"'))
                if self.kind == 'tier':
                    self.isequipped = flag.is_equipped()
                    self.ispurified = flag.is_purified()
                    self.tier_cb = QComboBox()
                    self.tier_cb.addItems(Tier.all_tags())
                    self.tier_cb.setCurrentText(flag.tag())
                    self.layout.addWidget(self.tier_cb)
                    self.equipped_cb = QCheckBox('is equipped')
                    self.equipped_cb.setChecked(flag.is_equipped())
                    self.layout.addWidget(self.equipped_cb)
                    self.purified_cb = QCheckBox('is purified')
                    self.purified_cb.setChecked(flag.is_purified())
                    self.layout.addWidget(self.purified_cb)
                self.layout.addWidget(self.buttonBox)
                self.setLayout(self.layout)

            def accept(self):
                tier = Tier(self.tier_cb.currentText(), self.equipped_cb.isChecked(), self.purified_cb.isChecked())
                self.parent()._person_wrapper.equipment[self.parent()._slot].flag = tier
                super().accept()
                
        item_name = wid.currentText()
        item = Fandom.all_by_name[item_name]
        if Fandom.is_equipment(item_name):
            dialog = Dialog(item, self)
            dialog.exec()


class Equipment(QWidget):
    def __init__(self, parent=None):
        self.person_wrapper: Optional[PersonWrapper] = None

        def setmodel(wid, typ):
            m = ItemModel.ItemModel()
            p = ItemModel.ItemProxy()
            p.setSourceModel(m)
            p.set_type(typ)
            self.vocation.currentTextChanged.connect(p.set_vocation)
            wid.setModel(p)
            wid.setModelColumn(1)
            wid.setCurrentIndex(-1)
            # wid.currentTextChanged.connect(lambda s: print(f'Equipment({typ}): Changed to "{s}"'))
            wid.customContextMenuRequested.connect(lambda pos: self.show_menu(wid, pos))
            wid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        super().__init__(parent)
        self.head: Optional[EquipmentCombo] = None
        self.torso: Optional[EquipmentCombo] = None
        self.chest: Optional[EquipmentCombo] = None
        self.pants: Optional[EquipmentCombo] = None
        self.boots: Optional[EquipmentCombo] = None
        self.arms: Optional[EquipmentCombo] = None
        self.jewel1: Optional[EquipmentCombo] = None
        self.primary: Optional[EquipmentCombo] = None
        self.cape: Optional[EquipmentCombo] = None
        self.jewel2: Optional[EquipmentCombo] = None
        self.secondary: Optional[EquipmentCombo] = None

        self.sex: Optional[QComboBox] = None
        self.vocation: Optional[QComboBox] = None

        here = path.dirname(path.realpath('__file__'))
        uic.loadUi(path.join(here, "Equipment.ui"), self)

        self.head.set_model('Head Armor')
        self.torso.set_model('Torso Armor')
        self.chest.set_model('Chest Clothing')
        self.pants.set_model('Leg Clothing')
        self.boots.set_model('Leg Armor')
        self.arms.set_model('Arms Armor')
        self.jewel1.set_model('Jewelry 1')
        self.primary.set_model('Primary Weapon')
        self.cape.set_model('Cloak')
        self.jewel2.set_model('Jewelry 2')
        self.secondary.set_model('Secondary Weapon')

        self.vocation.clear()
        # self.vocation.addItems(_vocations.keys())
        self.vocation.addItems(Vocations.vocations())

    def set_equipment(self, person_wrapper):
        self.person_wrapper = person_wrapper
        vocation = self.person_wrapper.vocation
        self.vocation.setCurrentText(Vocations.name(vocation))

        def set_equipment(tag: str, where: QComboBox):
            slot = self.person_wrapper.equipment[tag]
            what = slot.idx
            if what < 0:
                print(f'{tag}: UNEQUIPPED ({what})')
                where.setCurrentIndex(-1)
            else:
                name = Fandom.all_by_id[what]['Name']
                print(f'{tag}: {name} ({what})')
                where.setCurrentText(name)

        self.primary.set_equipment(self.person_wrapper, 'Primary Weapon')
        self.secondary.set_equipment(self.person_wrapper, 'Secondary Weapon')
        self.chest.set_equipment(self.person_wrapper, 'Chest Clothing')
        self.pants.set_equipment(self.person_wrapper, 'Leg Clothing')
        self.head.set_equipment(self.person_wrapper, 'Head Armor')
        self.torso.set_equipment(self.person_wrapper, 'Torso Armor')
        self.arms.set_equipment(self.person_wrapper, 'Arms Armor')
        self.boots.set_equipment(self.person_wrapper, 'Leg Armor')
        self.cape.set_equipment(self.person_wrapper, 'Cloak')
        self.jewel1.set_equipment(self.person_wrapper, 'Jewelry 1')
        self.jewel2.set_equipment(self.person_wrapper, 'Jewelry 2')

    def show_menu(self, wid, pos):
        class Dialog(QDialog):
            def __init__(self, equipment, parent=None):
                super().__init__(parent)
                self.setWindowTitle('Equipment details')
                self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                                  QDialogButtonBox.StandardButton.Cancel)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                self.layout = QVBoxLayout()
                message = QLabel(equipment['desc'])
                self.layout.addWidget(message)
                tier_cb = QComboBox()
                tier_cb.addItems(Tier.by_tag.keys())
                tier_cb.setCurrentText()
                self.layout.addWidget(self.buttonBox)
                self.setLayout(self.layout)

        item_name = wid.currentText()
        item = Fandom.all_by_name[item_name]
        if Fandom.is_equipment(item_name):
            dialog = Dialog(item, self)
            dialog.exec()


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
