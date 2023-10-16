import struct
import zlib
from typing import Optional

from PyQt6.QtCore import QObject, pyqtProperty, Qt, pyqtSignal
from PyQt6.QtGui import QCursor

import xml.etree.ElementTree as ET

from PyQt6.QtWidgets import QWidget


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


class DDDAfile(QObject):
    dataChanged = pyqtSignal()
    persChanged = pyqtSignal()
    pnamChanged = pyqtSignal(str)
    plevChanged = pyqtSignal(int)
    pvocChanged = pyqtSignal(int)
    pvolChanged = pyqtSignal(int)

    def __init__(self, parent: QWidget=None):
        super().__init__()
        self.valid = False
        self._parent = parent
        self._fname = ''
        self.data: Optional[ET.Element] = None
        self._pers = ''
        self.pdata: Optional[ET.Element] = None

    @pyqtProperty(str)
    def fname(self):
        return self._fname

    @fname.setter
    def fname(self, fname):
        if self._fname != fname:
            self.valid = False
            self._fname = fname
            if self._fname:
                self._parent.setCursor(QCursor(Qt.CursorShape.WaitCursor))
                with open(self._fname, "rb") as fi:
                    hdr = Header(fi)
                    buf = fi.read(hdr.compressedsize)
                xml = zlib.decompress(buf)
                xml = xml.decode()
                self.data = ET.fromstring(xml)
                if self.data is not None:
                    self.valid = True
                    self.dataChanged.emit()

    @pyqtProperty(str)
    def pretty(self):
        tree = ET.ElementTree(self.data)
        ET.indent(tree)
        return ET.tostring(tree.getroot()).decode()

    @pyqtProperty(str)
    def plain(self):
        tree = ET.ElementTree(self.data)
        ET.indent(tree, '')
        return ET.tostring(tree.getroot()).decode()

    def savex(self, fname='DDDA.sav'):
        tree = ET.ElementTree(self.data)
        ET.indent(tree)
        tree.write(fname)

    @pyqtProperty(str)
    def pers(self):
        return self._pers

    @pers.setter
    def pers(self, pers):
        if self._pers != pers:
            self._pers = pers
            self.pdata = None
            if pers == 'Player':
                self.pdata = self.data.find(".//class[@name='mPl']")
            elif pers == 'Main Pawn':
                self.pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[0]
            elif pers == 'Pawn A':
                self.pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[1]
            elif pers == 'Pawn B':
                self.pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[2]
            else:
                pass
            if self.pdata is None:
                print(f'{pers} not found')
            else:
                self.persChanged.emit()
                self.pnamChanged.emit(self.pname)
                self.plevChanged.emit(self.plevel)
                self.pvocChanged.emit(self.pvoc)
                self.pvolChanged.emit(self.pvol)

    @pyqtProperty(str)
    def pname(self):
        if self.pdata is None:
            return '???'
        else:
            name = ''
            for chx in self.pdata.findall('.//array[@name="(u8*)mNameStr"]/u8'):
                chv = chx.get('value')
                chi = int(chv)
                if chi > 0:
                    name += chr(chi)
            return name

    @pyqtProperty(int)
    def plevel(self):
        levx = self.pdata.find(".//u8[@name='mLevel']")
        if levx is None:
            return 0
        else:
            return int(levx.get('value'))

    @pyqtProperty(int)
    def pvoc(self):
        vocx = self.pdata.find(".//u8[@name='mJob']")
        if vocx is None:
            return 0
        else:
            return int(vocx.get('value'))

    @pyqtProperty(int)
    def pvol(self):
        volx = self.pdata.findall(".//array[@name='mJobLevel']/u8")
        if volx is None:
            return 0
        else:
            return int(volx[self.pvoc -1].get('value'))

