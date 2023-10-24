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
    pers_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.valid: bool = False
        self.dirty: bool = False
        self.data: Optional[et.Element] = None
        self._fname: Optional[str] = None

    def from_file(self, fname: str):
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


class ItemWrapper(QObject):
    def __init__(self, xclass: et.Element, parent=None):
        super().__init__(parent)
        self.xclass = xclass

    #@pyqtProperty(int)
    @property
    def idx(self):
        if int(self.xclass.find('./s16[@name="data.mNum"]').get('value')) > 0:
            return int(self.xclass.find('./s16[@name="data.mItemNo"]').get('value'))
        return -1

    # @pyqtProperty(int)
    @property
    def tier(self) -> int:
        if int(self.xclass.find('./s16[@name="data.mNum"]').get('value')) > 0:
            return int(self.xclass.find('./u32[@name="data.mFlag"]').get('value'))
        return -1


class EquipmentWrapper(QObject):
    def __init__(self, xarray: et.Element, parent=None):
        super().__init__(parent)
        self.xarray = xarray
        self.carray = self.xarray.findall('.//class[@type="sItemManager::cITEM_PARAM_DATA"]')
        if len(self.carray) != 12:
            print(f'Warning: {len(self.carray)} found (expected 12)')
        self.iarray = [ItemWrapper(c) for c in self.carray]

    @pyqtProperty(ItemWrapper)
    def primary(self):
        return self.iarray[0]

    @pyqtProperty(ItemWrapper)
    def secondary(self):
        return self.iarray[1]

    @pyqtProperty(ItemWrapper)
    def shirt(self):
        return self.iarray[2]

    @pyqtProperty(ItemWrapper)
    def pants(self):
        return self.iarray[3]

    @pyqtProperty(ItemWrapper)
    def helmet(self):
        return self.iarray[4]

    @pyqtProperty(ItemWrapper)
    def chest(self):
        return self.iarray[5]

    @pyqtProperty(ItemWrapper)
    def gauntlets(self):
        return self.iarray[6]

    @pyqtProperty(ItemWrapper)
    def greaves(self):
        return self.iarray[7]

    @pyqtProperty(ItemWrapper)
    def cape(self):
        return self.iarray[8]

    @pyqtProperty(ItemWrapper)
    def jewel1(self):
        return self.iarray[9]

    @pyqtProperty(ItemWrapper)
    def jewel2(self):
        return self.iarray[10]


class PersonWrapper(QObject):
    changed = pyqtSignal()
    name_changed = pyqtSignal(str)
    levl_changed = pyqtSignal(int)
    vocn_changed = pyqtSignal(int)
    vocl_changed = pyqtSignal(int)
    stor_changed = pyqtSignal()
    rowchanged = pyqtSignal(int)

    _persons = ['Player', 'Main Pawn', 'Pawn A', 'Pawn B', 'Storage']

    def __init__(self, wrapper: DDDAwrapper, who: str, parent=None):
        super().__init__(parent)
        self.wrapper = wrapper
        self.data = wrapper.data
        self._equipment: Optional[EquipmentWrapper] = None

        stores = self.data.findall('.//array[@name="mItem"]/class[@type="cSAVE_DATA_ITEM"]')

        pdata = None
        for n, person in enumerate(self._persons):
            if who == person:
                self._index = n
                match self._index:
                    case 0:
                        pdata = self.data.find(".//class[@name='mPl']")
                        self._store = stores[0].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = stores[0].find('./<u32[@name="mItemCount"]')
                    case 1:
                        pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[0]
                        self._store = stores[1].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = stores[1].find('./<u32[@name="mItemCount"]')
                    case 2:
                        pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[1]
                        self._store = stores[2].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = stores[2].find('./<u32[@name="mItemCount"]')
                    case 3:
                        pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[2]
                        self._store = stores[3].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = stores[3].find('./<u32[@name="mItemCount"]')
                    case 4:
                        self._store = self.data.findall('.//array[@name="mStorageItem"]/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = self.data.find('.//u32[@name="mStorageItemCount"]')
                    case _:
                        raise ValueError(f'Unknown person "{who}"')
                break
        if pdata is not None:
            self._equipment = EquipmentWrapper(pdata.find('.//array[@name="mEquipItem"]'))
            self._name = pdata.findall('.//array[@name="(u8*)mNameStr"]/u8')
            self._level = pdata.find(".//u8[@name='mLevel']")
            self._voc = pdata.find(".//u8[@name='mJob']")
            self._vlevels = pdata.findall(".//array[@name='mJobLevel']/u8")
        else:
            self._name = None
            self._level = None
            self._voc = None
            self._vlevels = None

    def _index_of_row(self, row):
        for n, r in enumerate(self._store):
            if r == row:
                return n
        return -1

    @pyqtProperty(str)
    def person(self):
        if self._name is not None:
            return self._persons[self._index]
        else:
            return None

    @pyqtProperty(str)
    def name(self) -> str:
        name = '???'
        if self._name is not None:
            name = ''
            for chx in self._name:
                chi = int(chx.get('value'))
                if chi > 0:
                    name += chr(chi)
        return name

    @pyqtProperty(int)
    def level(self):
        return int(self._level.get('value')) if self._level is not None else -1

    @level.setter
    def level(self, value: int):
        # TODO: check value is in range [1..200]
        if self._level is not None:
            self._level.set('value', str(value))

    @pyqtProperty(int)
    def vocation(self):
        return int(self._voc.get('value')) if self._voc is not None else -1

    @vocation.setter
    def vocation(self, value: int):
        # TODO: check value is in range [0..8]
        if self._voc is not None:
            self._voc.set('value', str(value))

    @pyqtProperty(int)
    def vocation_level(self):
        return int(self._vlevels[self.vocation-1].get('value')) if self._level is not None else -1

    @vocation_level.setter
    def vocation_level(self, value: int):
        # TODO: check value is in range [1..9]
        if self._vlevels is not None:
            self._vlevels[self.vocation-1].set('value', str(value))

    @pyqtProperty(EquipmentWrapper)
    def equipment(self):
        return self._equipment

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

    def row_inc(self, row, inc):
        idx = self._index_of_row(row)
        if idx < 0:
            print(f'ERROR: row not found ({row})')
            return
        num = self.row_num(row)
        n = num + inc
        if n > 0:
            row.find('./s16[@name="data.mNum"]').set('value', str(n))
        else:
            row.find('./s16[@name="data.mNum"]').set('value', "0")
            row.find('./s16[@name="data.mItemNo"]').set('value', "-1")
            row.find('./u32[@name="data.mFlag"]').set('value', "0")
            row.find('./u16[@name="data.mChgNum"]').set('value', "0")
            row.find('./u16[@name="data.mDay1"]').set('value', "0")
            row.find('./u16[@name="data.mDay2"]').set('value', "0")
            row.find('./u16[@name="data.mDay3"]').set('value', "0")
            row.find('./s8[@name="data.mMutationPool"]').set('value', "0")
            row.find('./s8[@name="data.mOwnerId"]').set('value', int(self._index))
            row.find('./u32[@name="data.mKey"]').set('value', "0")
            n = 0
        self.tot_inc(n - num)
        self.rowchanged.emit(idx)

    def add(self, idx):
        # FIXME: should check if similar row exists
        item = Fandom.all_by_id[idx]
        for n, row in enumerate(self._store):
            if self.row_num(row) == 0:
                row.find('./s16[@name="data.mNum"]').set('value', "1")
                row.find('./s16[@name="data.mItemNo"]').set('value', str(item['ID']))
                row.find('./u32[@name="data.mFlag"]').set('value', "1")
                row.find('./u16[@name="data.mChgNum"]').set('value', "0")
                row.find('./u16[@name="data.mDay1"]').set('value', "0")
                row.find('./u16[@name="data.mDay2"]').set('value', "0")
                row.find('./u16[@name="data.mDay3"]').set('value', "0")
                row.find('./s8[@name="data.mMutationPool"]').set('value', "0")
                row.find('./s8[@name="data.mOwnerId"]').set('value', int(self._index))
                row.find('./u32[@name="data.mKey"]').set('value', "0")
                self.tot_inc(1)
                self.rowchanged.emit(n)  # FIXME: this removes selection
                break

    def tot_inc(self, inc):
        if self._count is not None:
            count = int(self._count.get('value')) + inc
            self._count.set('value', str(count))


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

    player = PersonWrapper(ddda, 'Player')
    print(player.name, player.level, player.vocation, player.vocation_level)
    for row in player.rows:
        if player.row_valid(row):
            item = player.row_item(row)
            print(item, Fandom.all_by_id[item]['Name'],
                  player.row_num(row),
                  player.row_owner(row),
                  player.row_level(row))
    print('Primary Weapon', player.equipment.primary.idx, player.equipment.primary.tier)
    print('Secondary Weapon', player.equipment.secondary.idx)
    print('Clothing (shirt)', player.equipment.shirt.idx)
    print('Clothing (pants)', player.equipment.pants.idx)
    print('Helmet', player.equipment.helmet.idx)
    print('Chestplate', player.equipment.chest.idx)
    print('Gauntlets', player.equipment.gauntlets.idx)
    print('Greaves', player.equipment.greaves.idx)
    print('Cape', player.equipment.cape.idx)
    print('Jewel 1', player.equipment.jewel1.idx)
    print('Jewel 2', player.equipment.jewel2.idx)

    # ddda.to_xml_file()
    # ddda.to_file()
