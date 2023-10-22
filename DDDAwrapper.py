import shutil
import struct
import zlib
from collections import namedtuple
from os import path
from time import strftime, gmtime
from typing import Optional
from xml.etree import ElementTree as et

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty

import Fandom

Header = namedtuple('Header', ['u1', 'rsize', 'csize', 'u2', 'u3', 'u4', 'hash', 'u5'])


def _crc32(buf):
    crc = 0xffffffff
    for b in buf:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xedb88320 if crc & 1 else crc >> 1
    return crc


class DDDAwrapper(QObject):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.valid: bool = False
        self.dirty: bool = False
        self.data: Optional[et.Element] = None
        self._fname: Optional[str] = None

    def from_file(self, fname:str):
        if self._fname != fname:
            self.valid = False
            self._fname = fname
            if self._fname:
                with open(self._fname, "rb") as fi:
                    h = fi.read(32)
                    hdr = Header(*struct.unpack('<IIIIIIII', h))
                    buf = fi.read(hdr.csize)
                crc = _crc32(buf)
                if crc != hdr.hash:
                    raise ValueError(f'ERROR: hash mismatch ({crc} != {hdr.hash})')
                xml = zlib.decompress(buf)
                xml = xml.decode()
                self.data = et.fromstring(xml)
                if self.data is not None:
                    self.valid = True
                    self.dirty = False
                    self.data_changed.emit()

    def _backup(self, ext=None, fname=None):
        fname = fname or self._fname
        p, e = path.splitext(fname)
        if ext:
            fname = p + ext
        if path.isfile(fname):  # create backup if it doesn't exist
            ts = path.getmtime(fname)
            p, e = path.splitext(fname)
            sf = f"{p}-{strftime('%Y%m%d_%H%M%S', gmtime(ts))}{e}"
            if not path.isfile(sf):
                shutil.copy2(fname, sf)
        return fname

    def to_xml_file(self, fname: str=None):
        fname = self._backup('.xml', fname)
        sss = et.tostring(self.data).replace(b' />', b'/>')
        with open(fname, 'wb') as fo:
            fo.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
            fo.write(sss)
            fo.write(b'\n')

    def to_file(self, fname=None):
        fname = self._backup(fname=fname)
        sss = et.tostring(self.data).replace(b' />', b'/>')
        rsize = len(sss)
        z = zlib.compress(sss)
        crc = _crc32(z)
        hdr = Header(21, rsize, len(z), 860693325, 0, 860700740, crc, 1079398965)
        h = struct.pack('<IIIIIIII', *hdr)

        with open(fname, 'wb') as fo:
            fo.write(h)
            fo.write(z)
            fo.write(b'\0'*(524288 - len(h) - len(z)))


class PersonWrapper(QObject):
    changed = pyqtSignal()

    def __init__(self, wrwpper: DDDAwrapper, who: str, parent=None):
        super().__init__(parent)
        self.wrwpper = wrwpper
        self.data = wrwpper.data
        stores = self.data.findall('.//array[@name="mItem"]/class[@type="cSAVE_DATA_ITEM"]')
        match who:
            case 'Player':
                pdata = self.data.find(".//class[@name='mPl']")
                self._store = stores[0].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                self._count = None
            case 'Main Pawn':
                pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[0]
                self._store = stores[1].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                self._count = None
            case 'Pawn A':
                pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[1]
                self._store = stores[2].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                self._count = None
            case 'Pawn B':
                pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[2]
                self._store = stores[3].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                self._count = None
            case 'Store':
                pdata = None
                self._store = self.data.findall('.//array[@name="mStorageItem"]/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                self._count = self.data.find('.//u32[@name="mStorageItemCount"]')
            case _:
                raise ValueError(f'Unknown person "{who}"')
        if pdata is not None:
            self._name = pdata.findall('.//array[@name="(u8*)mNameStr"]/u8')
            self._level = pdata.find(".//u8[@name='mLevel']")
            self._voc = pdata.find(".//u8[@name='mJob']")
            self._vlevels = pdata.findall(".//array[@name='mJobLevel']/u8")
        else:
            self._name = None
            self._level = None
            self._voc = None
            self._vlevels = None

    @pyqtProperty(str)
    def name(self):
        if self._name is not None:
            name = ''
            for chx in self._name:
                chi = int(chx.get('value'))
                if chi > 0:
                    name += chr(chi)
            return name
        return '???'

    @pyqtProperty(int)
    def level(self):
        return int(self._level.get('value')) if self._level is not None else -1

    @pyqtProperty(int)
    def vocation(self):
        return int(self._voc.get('value')) if self._voc is not None else -1

    @pyqtProperty(int)
    def vocation_level(self):
        return int(self._vlevels[self.vocation-1].get('value')) if self._level is not None else -1

    @pyqtProperty(int)
    def rows(self):
        return self._store

    @staticmethod
    def row_num(row):
        return int(row.find('./s16[@name="data.mNum"]').get('value'))

    @staticmethod
    def row_valid(row):
        return PersonWrapper.row_num(row) > 0

    @staticmethod
    def row_item(row):
        return int(row.find('./s16[@name="data.mItemNo"]').get('value'))

    @staticmethod
    def row_level(row):
        return int(row.find('./u32[@name="data.mFlag"]').get('value'))

    @staticmethod
    def row_owner(row):
        return int(row.find('./s8[@name="data.mOwnerId"]').get('value'))


class InventoryWrapper(QObject):
    changed = pyqtSignal()

    def __init__(self, wrwpper: DDDAwrapper, root=et.Element, parent=None):
        super().__init__(parent)
        self.wrwpper = wrwpper
        self.root = root

    def rows(self):
        return None

    def edit(self, idx: int, add: int):
        pass


if __name__ == '__main__':
    ddda = DDDAwrapper()
    ddda.from_file('/tmp/t/DDDA.sav')

    player = PersonWrapper(ddda, 'Pawn B')
    print(player.name, player.level, player.vocation, player.vocation_level)
    for row in player.rows:
        if player.row_valid(row):
            item = player.row_item(row)
            print(item, Fandom.all_by_id[item]['Name'],
                  player.row_num(row),
                  player.row_owner(row),
                  player.row_level(row))
    # ddda.to_xml_file()
    # ddda.to_file()
