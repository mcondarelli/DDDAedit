from os import path
from typing import Optional

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QComboBox

import SplitItemModel


_vocations = {
    'Fighter': {'primary': 'Swords', 'secondary': 'Shields'},
    'Strider': {'primary': 'Daggers', 'secondary': 'Shortbows'},
    'Mage': {'primary': 'Staess', 'secondary': 'None'},
    'Assassin': {'primary': ['Swords', 'Daggers'], 'secondary': ['Shields', 'Shortbows']},
    'MagicK Archer': {'primary': ['Staves', 'Daggers'], 'secondary': 'Magick Bows'},
    'Mystic Knight': {'primary': ['Swords', 'Staves', 'Maces'], 'secondary': 'Magick Shields'},
    'Warrior': {'primary': ['Longswords', 'Warhammers'], 'secondary': 'Shields'},
    'Ranger': {'primary': 'Daggers', 'secondary': 'Longbows'},
    'Sorcerer': {'primary': 'Archistaves', 'secondary': 'None'}
}


class Equipment(QWidget):
    def __init__(self):
        def setmodel(wid, typ):
            m = SplitItemModel.SplitItemModel(typ)
            p = SplitItemModel.SplitItemProxy()
            p.setSourceModel(m)
            wid.setModel(p)

        super().__init__()
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
        self.vocation.addItems(_vocations.keys())


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
