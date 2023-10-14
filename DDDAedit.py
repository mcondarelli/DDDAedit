# import pprint
import struct
import zlib
from typing import Optional
import xml.etree.ElementTree as ET

# import xmltodict
from PyQt6 import uic, QtWidgets, QtCore, QtGui

import sys

import picwidgets


class Header:
    # unsigned int u1;       //Version (21 for DDDA console and DDDA PC, and 5 for original DD on console)
    # unsigned int realSize; //Real size of compressed save game data
    # unsigned int compressedSize;
    # unsigned int u2;       //Always 860693325
    # unsigned int u3;       //Always 0
    # unsigned int u4;       //Always 860700740
    # unsigned int hash;     //Checksum of compressed save data
    # unsigned int u5;       //Always 1079398965

    def __init__(self, fi):
        buf = fi.read(4*8)
        self.u1: int = 0
        self.realsize: int = 0
        self.compressedsize: int = 0
        self.u2: int = 0
        self.u3: int = 0
        self.u4: int = 0
        self.hash: int = 0
        self.u5: int = 0
        self.u1, self.realsize, self.compressedsize, self.u2, self.u3, self.u4, self.hash, self.u5 = (
            struct.unpack('<IIIIIIII', buf))
        if self.u1 != 21 or self.u2 != 860693325 or self.u3 != 0 or self.u4 != 860700740 or self.u5 != 1079398965:
            raise AssertionError('Bad header')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dddasav: Optional[QtWidgets.QLineEdit] = None
        self.load: Optional[QtWidgets.QPushButton] = None
        self.xml: Optional[QtWidgets.QPlainTextEdit] = None
        self.pers: Optional[QtWidgets.QComboBox] = None
        self.name: Optional[QtWidgets.QLabel] = None
        self.level: Optional[QtWidgets.QSpinBox] = None
        self.vocations: Optional[QtWidgets.QWidget] = None
        uic.loadUi("DDDAedit.ui", self)
        self.data: Optional[ET.Element] = None

        vocations = picwidgets.PicGrid(
            [['resources/DDicon_fighter.webp', 'resources/DDicon_strider.webp', 'resources/DDicon_mage.webp'],
             ['resources/DDicon_assassin.webp', 'resources/DDicon_magicarcher.webp', 'resources/DDicon_magicknight.webp'],
             ['resources/DDicon_warrior.webp', 'resources/DDicon_ranger.webp', 'resources/DDicon_sorcerer.webp']
            ])
        self.vocations.parent().layout().replaceWidget(self.vocations, vocations)
        vocations.selec.connect(self.on_vocation_selec)

    def on_vocation_selec(self, param):
        print(param)

    @QtCore.pyqtSlot()
    def on_load_clicked(self):
        if self.load.text() == "Select":
            self.load.setText("Load")
            qfd = QtWidgets.QFileDialog()
            qfd.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
            qfd.setNameFilter("Savefiles (*.sav)")
            if qfd.exec():
                self.dddasav.setText(qfd.selectedFiles()[0])
        elif self.load.text() == "Load":
            self.load.setText("Save")
            self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.WaitCursor))
            with open(self.dddasav.text(), "rb") as fi:
                hdr = Header(fi)
                buf = fi.read(hdr.compressedsize)
            xml = zlib.decompress(buf)
            xml = xml.decode()
            self.data = ET.fromstring(xml)
            # ET.indent(self.data)
            self.xml.setPlainText(ET.tostring(self.data).decode())
            self.unsetCursor()
        else:
            self.load.setText("Select")
            # dic = xmltodict.parse(self.xml.toPlainText())
            # self.xml.setPlainText(pprint.pformat(dic, 4))
            if self.data:
                tree = ET.ElementTree(self.data)
                ET.indent(tree)
                tree.write('DDDA.xml')
                self.xml.setPlainText(ET.tostring(self.data).decode())

    @QtCore.pyqtSlot(str)
    def on_pers_currentTextChanged(self, txt):
        pers = None
        if txt == 'Player':
            pers = self.data.find(".//class[@name='mPl']")
        elif txt == 'Main Pawn':
            pers = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[0]
        elif txt == 'Pawn A':
            pers = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[1]
        elif txt == 'Pawn B':
            pers = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[2]
        else:
            pass
        if pers is None:
            print(f'{txt} not found')
        else:
            name = ''
            for chx in pers.findall('.//array[@name="(u8*)mNameStr"]/u8'):
                chv = chx.get('value')
                chi = int(chv)
                if chi > 0:
                    name += chr(chi)
            self.name.setText(name or '???')
            levx = pers.find(".//u8[@name='mLevel']")
            if levx is not None:
                levv = levx.get('value')
                levi = int(levv)
                self.level.setValue(levi)


def main():
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
