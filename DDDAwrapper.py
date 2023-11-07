import shutil
import struct
import zlib
from collections import namedtuple
from os import path
from time import strftime, gmtime
from typing import Optional
from xml.etree import ElementTree as ET

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty

import Fandom

Header = namedtuple('Header', ['u1', 'rsize', 'csize', 'u2', 'u3', 'u4', 'hash', 'u5'])


class Flag:
    def __init__(self, typ='invalid'):
        self.kind = typ

    def idx(self):
        return -1

    def tag(self):
        return 'UNKNOWN'


class Tier(Flag):
    _tiers = [(0x0001, 'no stars'),         #   3 0003 0000 + 3
              (0x0009, '1 star'),           #  13 000D 0008 + 5
              (0x0011, '2 stars'),          #  19 0013 0010 + 3
              (0x0021, '3 stars'),          #  35 0023 0020 + 3
              (0x0041, 'dragonforged'),     #  67 0043 0040 + 3
              (0x0201, 'silver forged'),    # 515 0203 0200 + 3
              (0x0401, 'gold forged')]      #1027 0403 0400 + 3
    _by_id = {x[0]: x[1] for x in _tiers}
    _by_tag = {x[1]: x[0] for x in _tiers}

    def __init__(self, tier, equip=None, purified=None):
        super().__init__('tier')
        if isinstance(tier, str):
            if tier.isnumeric():
                tier = int(tier)
            else:
                self._tag = tier
                self._idx = Tier._by_tag[tier]
                self._equipped = equip
                self._purified = purified
                return
        if isinstance(tier, int):
            self._purified = (tier & 0x80) != 0
            self._equipped = (tier & 2) != 0
            self._idx = tier & ~0x82
            self._tag = Tier._by_id[self._idx]
        else:
            raise ValueError(f'ERROR: unexpected type {type(tier).__name__}')

    def idx(self):
        idx = self._idx
        if self._equipped:
            idx |= 2
        if self._purified:
            idx |= 0x80
        return idx

    def tag(self):
        return self._tag

    @staticmethod
    def all_tags():
        return [x[1] for x in Tier._tiers]

    def is_purified(self):
        return bool(self._purified)

    def is_equipped(self):
        return bool(self._equipped)


class Jewel(Flag):
    def __init__(self, flag):
        super().__init__('jewel')
        self._flag = flag
        # TODO: parse jewelry flags

    def idx(self):
        return self._flag

    def tag(self):
        return str(self._flag)

def _crc32(buf):
    crc = 0xffffffff
    for b in buf:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xedb88320 if crc & 1 else crc >> 1
    return crc


class DDDAwrapper(QObject):
    """
    Wrapper class for the whole DDDA.sav file.
    It is composed by many sections, only a few of them are currently handled:
    - There are 4 "persons":
      - the Player
      - the Main Pawn
      - Pawn A, if any, hired from the Rift
      - Pawn B, if any, hired from the Rift
    - each Person has several editable fields:
      - Name
      - Level
      - Vocation
      - Vocation affinity
      - personal (equipped) Equipment
      - personal Inventory
    - Global Storage (accessed through "inns")
    - Money
    - Rift Crystals

    Underlaying structure is a huge XML file (compressed and CRC validated on disk)
    which is edited "in place".
    Each subclass holds a pointer (`lxml.Element`) to the relevant section of XML.
    """
    data_changed = pyqtSignal()
    pers_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        """
        Initaialize an empty structure.
        Note: there is currently *NO WAY* to initialize actual content
        without an on-disc file produced by DDDA.

        :param parent: QObject parent, currently unused
        """
        super().__init__(parent)
        self.persons = None
        self.original_xml = None
        self.valid: bool = False
        self.dirty: bool = False
        self.data: Optional[ET.Element] = None
        self._fname: Optional[str] = None

    def from_file(self, fname: str):
        """
        Read a `DDDA.sav` savefile from disk.



        It may `raise` `ValueError` exception in case file is corrupted.

        :param fname: Name of the file to read
        :return: Nothing
        """
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
                self.data = ET.fromstring(xml)
                if self.data is not None:
                    self.valid = True
                    self.dirty = False
                    self.data_changed.emit()
                    self.original_xml = xml
                    self.persons = PersonWrapper.parse(self)

    def _to_xml(self):
        xml = b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(self.data).replace(b' />', b'/>')
        return xml

    def compute_diff_table(self, callback):
        xml = self._to_xml().decode()
        for n, (old, new) in enumerate(zip(self.original_xml.splitlines(), xml.splitlines())):
            if old != new:
                callback(n, old, new)

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

    def to_xml_file(self, fname: str = None):
        fname = self._backup('.xml', fname)
        sss = self._to_xml()
        with open(fname, 'wb') as fo:
            fo.write(sss)
            fo.write(b'\n')

    def to_file(self, fname=None):
        fname = self._backup(fname=fname)
        sss = self._to_xml()  # et.tostring(self.data).replace(b' />', b'/>')
        rsize = len(sss)
        z = zlib.compress(sss)
        crc = _crc32(z)
        hdr = Header(21, rsize, len(z), 860693325, 0, 860700740, crc, 1079398965)
        h = struct.pack('<IIIIIIII', *hdr)

        with open(fname, 'wb') as fo:
            fo.write(h)
            fo.write(z)
            fo.write(b'\0' * (524288 - len(h) - len(z)))

    def person(self, name):
        return self.persons[name]


class ItemWrapper(QObject):
    def __init__(self, xclass: ET.Element, parent):
        super().__init__(parent)
        self.xclass = xclass
        self.equipped = isinstance(parent, EquipmentWrapper)
        self._idx = None
        self._type = None

    def _is_valid(self):
        return int(self.xclass.find('./s16[@name="data.mNum"]').get('value')) > 0

    def _get_idx(self):
        if self._idx is None:
            if self._is_valid():
                self._idx = int(self.xclass.find('./s16[@name="data.mItemNo"]').get('value'))
        return self._idx

    def _get_type(self):
        if self._type is None:
            idx = self._get_idx()
            if idx is not None:
                self._type = Fandom.all_by_id[self.idx]['Type']
        return self._type

    def is_armor(self):
        item_type = self._get_type()
        return item_type in [
            'Arms Armor',
            'Chest Clothing',
            'Cloak',
            'Head Armor',
            'Leg Armor',
            'Leg Clothing',
            'Torso Armor',
        ]

    def is_weapon(self):
        item_type = self._get_type()
        return item_type in [
            'Archistaves',
            'Daggers',
            'Longbows',
            'Longswords',
            'Maces',
            'Magick Bows',
            'Magick Shields',
            'Shields',
            'Shortbows',
            'Staves',
            'Swords',
            'Warhammers',
        ]

    def is_equipment(self):
        return self.is_armor() or self.is_weapon()

    def is_jewel(self):
        item_type = self._get_type()
        return item_type in ['Jewelry']

    # @pyqtProperty(int)
    @property
    def idx(self):
        # if int(self.xclass.find('./s16[@name="data.mNum"]').get('value')) > 0:
        #     return int(self.xclass.find('./s16[@name="data.mItemNo"]').get('value'))
        # return -1
        idx = self._get_idx()
        return idx if idx is not None else -1

    # @pyqtProperty(int)
    @property
    def flag(self) -> Flag:
        if self._is_valid():
            value = int(self.xclass.find('./u32[@name="data.mFlag"]').get('value'))
            if self.is_equipment():
                return Tier(value)
            elif self.is_jewel():
                return Jewel(value)
        return None

    @flag.setter
    def flag(self, tier: Flag):
        if tier is not None:
            self.xclass.find('./u32[@name="data.mFlag"]').set('value', str(tier.idx()))

    @property
    def flag_name(self):
        return self.flag.tag()

    @property
    def flag_kind(self):
        return self.flag.kind


class EquipmentWrapper(QObject):
    _slots = [
        'Primary Weapon',
        'Secondary Weapon',
        'Chest Clothing',
        'Leg Clothing',
        'Head Armor',
        'Torso Armor',
        'Arms Armor',
        'Leg Armor',
        'Cloak',
        'Jewelry 1',
        'Jewelry 2',
    ]

    def __init__(self, xarray: ET.Element, parent):
        super().__init__(parent)
        self.xarray = xarray
        self.carray = self.xarray.findall('.//class[@type="sItemManager::cITEM_PARAM_DATA"]')
        if len(self.carray) != 12:
            print(f'Warning: {len(self.carray)} found (expected 12)')
        self.slots = {slot: ItemWrapper(xclass, self) for slot, xclass in zip(self._slots, self.carray)}

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.slots[item]
        elif isinstance(item, int):
            return self.slots[self._slots[item]]
        else:
            raise IndexError(f'Error: unknown index {item} ({type(item).__name__})')

    @pyqtProperty(QObject)  # FIXME: it should be (PersonWrapper)
    def owner(self):
        return self.parent()

    def dump(self):
        for name, data in self.slots.items():
            if data.idx >= 0:
                print(f'    {name:>20s} : {Fandom.all_by_id[data.idx]["Name"]:>25s} : {data.flag}')
        print(f'------------------------------------------------------------------------------------')


class PersonWrapper(QObject):
    changed = pyqtSignal()
    name_changed = pyqtSignal(str)
    levl_changed = pyqtSignal(int)
    vocn_changed = pyqtSignal(int)
    vocl_changed = pyqtSignal(int)
    stor_changed = pyqtSignal()
    rowchanged = pyqtSignal(int)

    _persons = ['Player', 'Main Pawn', 'Pawn A', 'Pawn B', 'Storage']

    @staticmethod
    def parse(wrapper: DDDAwrapper):
        return {person: PersonWrapper(wrapper, person) for person in PersonWrapper._persons}

    def __init__(self, wrapper: DDDAwrapper, who: str):
        super().__init__(wrapper)
        self.wrapper = wrapper
        self.data = wrapper.data
        self._who = who
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
                        self._count = stores[0].find('./u32[@name="mItemCount"]')
                    case 1:
                        pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[0]
                        self._store = stores[1].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = stores[1].find('./u32[@name="mItemCount"]')
                    case 2:
                        pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[1]
                        self._store = stores[2].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = stores[2].find('./u32[@name="mItemCount"]')
                    case 3:
                        pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[2]
                        self._store = stores[3].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = stores[3].find('./u32[@name="mItemCount"]')
                    case 4:
                        self._store = self.data.findall(
                            './/array[@name="mStorageItem"]/class[@type="sItemManager::cITEM_PARAM_DATA"]')
                        self._count = self.data.find('.//u32[@name="mStorageItemCount"]')
                    case _:
                        raise ValueError(f'Unknown person "{who}"')
                break
        if pdata is not None:
            self._equipment = EquipmentWrapper(pdata.find('.//array[@name="mEquipItem"]'), self)
            self._name = pdata.findall('.//array[@name="(u8*)mNameStr"]/u8')
            self._level = pdata.find(".//u8[@name='mLevel']")
            self._voc = pdata.find(".//u8[@name='mJob']")
            self._vlevels = pdata.findall(".//array[@name='mJobLevel']/u8")
        else:
            self._name = None
            self._level = None
            self._voc = None
            self._vlevels = None

        self.dump()

    def dump(self):
        print(f'===== {self._who}: {self.name} =======================================================')
        if self._equipment is not None:
            self._equipment.dump()
        for row in self._store:
            if self.row_valid(row):
                print(f'    {self.row_item(row):04d} : {Fandom.all_by_id[self.row_item(row)]["Name"]:>25s} : {self.row_flag(row)}')
        print(f'------------------------------------------------------------------------------------')
        print()

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
        return int(self._vlevels[self.vocation - 1].get('value')) if self._level is not None else -1

    @vocation_level.setter
    def vocation_level(self, value: int):
        # TODO: check value is in range [1..9]
        if self._vlevels is not None:
            self._vlevels[self.vocation - 1].set('value', str(value))

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
    def row_flag(row):
        return int(row.find('./u32[@name="data.mFlag"]').get('value'))

    @staticmethod
    def row_set_flag(row, value: int):
        row.find('./u32[@name="data.mFlag"]').set('value', str(value))

    @staticmethod
    def row_owner(row):
        return int(row.find('./s8[@name="data.mOwnerId"]').get('value'))

    def row_inc(self, row, inc):
        idx = self._store.index(row)
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
            row.find('./s8[@name="data.mOwnerId"]').set('value', "0")  # str(self._index))
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
                row.find('./s8[@name="data.mOwnerId"]').set('value', "0")  # str(self._index)) != "0" for EQUIPPED items
                row.find('./u32[@name="data.mKey"]').set('value', "0")
                self.tot_inc(1)
                self.rowchanged.emit(n)  # FIXME: this removes selection
                break

    def tot_inc(self, inc):
        if self._count is not None:
            count = int(self._count.get('value')) + inc
            self._count.set('value', str(count))


if __name__ == '__main__':
    ddda = DDDAwrapper()
    ddda.from_file('/tmp/t/DDDA.sav')

    player = ddda.person('Main Pawn')
    print(player.name, player.level, player.vocation, player.vocation_level)
    for row in player.rows:
        if player.row_valid(row):
            item = player.row_item(row)
            print(item, Fandom.all_by_id[item]['Name'],
                  player.row_num(row),
                  player.row_owner(row),
                  player.row_flag(row))
    print('Primary Weapon', player.equipment.primary.idx, player.equipment.primary.flag)
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
