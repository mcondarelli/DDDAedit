import struct
import zlib
import sys
from typing import Optional
import xml.etree.ElementTree as ET

from PyQt6 import uic, QtWidgets, QtCore, QtGui

import picwidgets


class Pers(QtWidgets.QWidget):
    vocs = ['resources/DDicon_fighter.webp',
            'resources/DDicon_strider.webp',
            'resources/DDicon_mage.webp',
            'resources/DDicon_assassin.webp',
            'resources/DDicon_magicarcher.webp',
            'resources/DDicon_magicknight.webp',
            'resources/DDicon_warrior.webp',
            'resources/DDicon_ranger.webp',
            'resources/DDicon_sorcerer.webp']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        vl = QtWidgets.QGridLayout()
        self.setLayout(vl)
        l1 = QtWidgets.QLabel('name')
        vl.addWidget(l1, 0, 0)
        self.name = QtWidgets.QLineEdit()
        self.name.setReadOnly(True)
        vl.addWidget(self.name, 0, 1)
        l1 = QtWidgets.QLabel('level')
        vl.addWidget(l1, 0, 2)
        self.level = QtWidgets.QSpinBox()
        vl.addWidget(self.level, 0, 3)
        self.vo = picwidgets.PicGrid(
            [[Pers.vocs[0], Pers.vocs[1], Pers.vocs[2]],
             [Pers.vocs[3], Pers.vocs[4], Pers.vocs[5]],
             [Pers.vocs[6], Pers.vocs[7], Pers.vocs[8]]
             ])
        self.vo.selec.connect(self.on_vocation_selec)
        vl.addWidget(self.vo, 1, 0, 2, 3)
        se = picwidgets.StarEditor(max_count=9)
        # se.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding,QSizePolicy.Policy.Minimum))
        se.editing_finished.connect(self.on_vocation_level)
        vl.addWidget(se, 1, 3)

    def enable(self, data):
        self.data = data
        self.setEnabled(bool(data))

    def set_pers(self, pers):
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

        vocx = pers.find(".//u8[@name='mJob']")
        if vocx is not None:
            voc = int(vocx.get('value'))
            print(voc)
            self.vo.select(voc)

    def on_vocation_selec(self, param):
        print(param)

    def on_vocation_level(self, level):
        print(level)


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
        buf = fi.read(4 * 8)
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
        self.xml: Optional[QtWidgets.QPlainTextEdit] = None
        self.main: Optional[QtWidgets.QWidget] = None
        self.pers: Optional[QtWidgets.QComboBox] = None
        self.pers_commit: Optional[QtWidgets.QPushButton] = None
        self.vocations: Optional[Pers] = None
        self.actionOpen: Optional[QtGui.QAction] = None
        self.actionSave: Optional[QtGui.QAction] = None
        self.actionSavex: Optional[QtGui.QAction] = None
        uic.loadUi("DDDAedit.ui", self)
        self.data: Optional[ET.Element] = None

        self.actionOpen.triggered.connect(self.on_open_triggered)
        self.actionSavex.triggered.connect(self.on_savex_triggered)

        self.edit_action = QtGui.QAction(QtGui.QIcon.fromTheme("text-editor"), 'Edit...')
        self.edit_action.triggered.connect(self.on_dddasav_edit)

        self.load_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-open"), 'Open...')
        self.load_action.triggered.connect(self.on_dddasav_load)

        self.dddasav.setPlaceholderText('Find your save file')
        self.dddasav.addAction(self.edit_action, QtWidgets.QLineEdit.ActionPosition.TrailingPosition)

        self.settings = QtCore.QSettings("MCondarelli", "DDDAsav")
        file = self.settings.value('file/savefile')
        if file:
            self.dddasav.setText(file)
            self.on_dddasav_load()

    def on_dddasav_edit(self):
        qfd = QtWidgets.QFileDialog()
        qfd.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        qfd.setNameFilter("Savefiles (*.sav)")
        if qfd.exec():
            self.dddasav.setText(qfd.selectedFiles()[0])
        self.dddasav.removeAction(self.load_action)
        if self.dddasav.text():
            self.dddasav.addAction(self.load_action, QtWidgets.QLineEdit.ActionPosition.TrailingPosition)
            self.settings.setValue('file/savefile', self.dddasav.text())

    def on_open_triggered(self):
        if not self.dddasav.text():
            self.on_dddasav_edit()
        if self.dddasav.text():
            self.on_dddasav_load()

    def on_dddasav_load(self):
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
        self.main.setEnabled(True)
        self.actionSavex.setEnabled(True)
        self.vocations.enable(self.data)

    @QtCore.pyqtSlot()
    def on_savex_triggered(self):
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
            self.vocations.set_pers(pers)


def main():
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
