import pprint
import shutil
import struct
import zlib
from os import path
from time import strftime, gmtime
from typing import Optional

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal

import xml.etree.ElementTree as ET

from PyQt6.QtWidgets import QWidget

from Fandom import all_by_id

vocations = ['fighter',
             'striderp',
             'DDicon_mage',
             'assassin',
             'magicarcher',
             'magicknight',
             'warrior',
             'ranger',
             'sorcerer']

augments = ['Fitness',
            'Sinew',
            'Egression',
            'Prescience',
            'Exhilaration',
            'Vehemence',
            'Vigilance',
            'Leg-Strength',
            'Arm-Strength',
            'Grit',
            'Damping',
            'Dexterity',
            'Eminence',
            'Endurance',
            'Infection',
            'Equanimity',
            'Beatitude',
            'Perpetuation',
            'Intervention',
            'Attunement',
            'Apotropaism',
            'Adamance',
            'Periphery',
            'Sanctuary',
            'Restoration',
            'Retribution',
            'Reinforcement',
            'Fortitude',
            'Watchfulness',
            'Preemption',
            'Autonomy',
            'Bloodlust',
            'Entrancement',
            'Sanguinity',
            'Toxicity',
            'Resilience',
            'Resistance',
            'Detection',
            'Regeneration',
            'Allure',
            'Potential',
            'Magnitude',
            'Temerity',
            'Audacity',
            'Proficiency',
            'Ferocity',
            'Impact',
            'Bastion',
            'Clout',
            'Trajectory',
            'Morbidity',
            'Precision',
            'Stability',
            'Efficacy',
            'Radiance',
            'Longevity',
            'Gravitas',
            'Articulacy',
            'Conservation',
            'Emphasis',
            'Suasion',
            'Acuity',
            'Awareness',
            'Suasion',
            'Thrift',
            'Weal',
            'Renown']

tier_by_id = {
    1: "No Stars",
    3: "Tier 0",
    13: "Tier 1",
    19: "Tier 2",
    35: "Tier 3",
    67: "Dragon red",
    512: "Dragon silver",
    1027: "Dragon gold"
}

tier_by_name = {n: i for i, n in tier_by_id.items()}


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
    dataChanged = pyqtSignal(ET.Element)
    persChanged = pyqtSignal(int)
    pnamChanged = pyqtSignal(str)
    plevChanged = pyqtSignal(int)
    pvocChanged = pyqtSignal(int)
    pvolChanged = pyqtSignal(int)
    storChanged = pyqtSignal()

    def __init__(self, parent: QWidget = None):
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
                with open(self._fname, "rb") as fi:
                    hdr = Header(fi)
                    buf = fi.read(hdr.compressedsize)
                xml = zlib.decompress(buf)
                xml = xml.decode()
                self.data = ET.fromstring(xml)
                if self.data is not None:
                    self.valid = True
                    self.dataChanged.emit(self.data)

    @pyqtProperty(str)
    def pretty(self):
        tree = ET.ElementTree(self.data)
        ET.indent(tree)
        return ET.tostring(tree.getroot()).decode()

    @pyqtProperty(str)
    def plain(self):
        def tokenize(e):
            for x in ET.tostringlist(e):
                yield x.strip()
        txt = b"\n".join(tokenize(self.data))
        return txt

    def savex(self, fname='DDDA.xml'):
        tree = ET.ElementTree(self.data)
        ET.indent(tree)
        tree.write(fname)

    def save(self, fname='DDDA.sav'):
        def crc32(block):
            table = [0] * 256
            for c in range(256):
                x = c
                b = 0
                for _ in range(8):
                    if x & 1:
                        x = ((x >> 1) ^ 0xEDB88320)
                    else:
                        x >>= 1
                table[c] = x
            x = -1
            for c in block:
                x = (( x >> 8) ^ table[((x ^ c) & 255)])
            return x
        def crc32_(msg):  # ERROR: hash mismatch (2864440309 != 1430526986)
            crc = 0xffffffff
            for b in msg:
                crc ^= b
                for _ in range(8):
                    crc = (crc >> 1) ^ 0xedb88320 if crc & 1 else crc >> 1
            return crc ^ 0xffffffff

        tree = self.plain
        if path.isfile(fname):  # create backup if it doesn't exist
            ts = path.getmtime(fname)
            p, e = path.splitext(fname)
            sf = f"{p}-{strftime('%Y%m%d_%H%M%S', gmtime(ts))}{e}"
            if not path.isfile(sf):
                shutil.move(fname, sf)
        realsize = len(tree)
        z = zlib.compress(tree)
        compressedsize = len(z)
        crc = crc32(z)
        h = struct.pack('<IIIIIIII',21, realsize, compressedsize, 860693325, 0, 860700740, crc, 1079398965)
        with open(fname, 'wb') as fo:
            fo.write(h)
            fo.write(z)
            fo.write(b'\0'*(524288 - len(h) - compressedsize))

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
                pidx = 0
            elif pers == 'Main Pawn':
                self.pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[0]
                pidx = 1
            elif pers == 'Pawn A':
                self.pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[1]
                pidx = 2
            elif pers == 'Pawn B':
                self.pdata = self.data.find(".//class[@type='cSAVE_DATA_CMC']/..[@name='mCmc']")[2]
                pidx = 3
            else:
                pidx = -1
                pass
            if self.pdata is None:
                print(f'{pers} not found')
            else:
                self.persChanged.emit(pidx)
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
            return int(volx[self.pvoc - 1].get('value'))

    def store(self):
        """
<u32 name="mStorageItemCount" value="#"/> - Number of Items in Storage
<array name="mStorageItem" type="class" count="4278">
    <class type="sItemManager::cITEM_PARAM_DATA">
        <s16 name="data.mNum" value="#"/> - Item Quantity 1
        <s16 name="data.mItemNo" value="#"/> - Item ID
        <u32 name="data.mFlag" value="#"/> - Item Level/Tier - Tier ID list below
        <u16 name="data.mChgNum" value="0"/> - UNKNOWN
        <u16 name="data.mDay1" value="#"/> - Item Quantity 2 - 2, 3 and 4 HAVE to equal Item Quantity 1
        <u16 name="data.mDay2" value="#"/> - Item Quantity 3 - 2, 3 and 4 HAVE to equal Item Quantity 1
        <u16 name="data.mDay3" value="#"/> - Item Quantity 4 - 2, 3 and 4 HAVE to equal Item Quantity 1
        <s8 name="data.mMutationPool" value="0"/> - UNKNOWN
        <s8 name="data.mOwnerId" value="#"/> - Who the Item belongs to, 0= Main Character, 1= Main Pawn, etc.
        <u32 name="data.mKey" value="0"/> - UNKNOWN
    </class>
    <class type="sItemManager::cITEM_PARAM_DATA"> - BLANK ITEM/NO ITEM
        <s16 name="data.mNum" value="0"/>
        <s16 name="data.mItemNo" value="-1"/>
        <u32 name="data.mFlag" value="0"/>
        <u16 name="data.mChgNum" value="0"/>
        <u16 name="data.mDay1" value="0"/>
        <u16 name="data.mDay2" value="0"/>
        <u16 name="data.mDay3" value="0"/>
        <s8 name="data.mMutationPool" value="0"/>
        <s8 name="data.mOwnerId" value="0"/>
        <u32 name="data.mKey" value="0"/>
    </class>
</array>

        :return:
        """
        count = self.data.find('.//u32[@name="mStorageItemCount"]').get('value')
        count = int(count)
        aryx = self.data.find('.//array[@name="mStorageItem"]')
        ary = aryx.findall('./class[@type="sItemManager::cITEM_PARAM_DATA"]')
        sto = []
        sum = 0
        for a in ary:
            num = int(a.find('./s16[@name="data.mNum"]').get('value'))
            if num > 0:
                idx = int(a.find('./s16[@name="data.mItemNo"]').get('value'))
                lev = int(a.find('./u32[@name="data.mFlag"]').get('value'))
                no1 = int(a.find('./u16[@name="data.mDay1"]').get('value'))
                no2 = int(a.find('./u16[@name="data.mDay2"]').get('value'))
                no3 = int(a.find('./u16[@name="data.mDay3"]').get('value'))
                own = int(a.find('./s8[@name="data.mOwnerId"]').get('value'))
                if num != no1 or num != no2 or num != no3:
                    print(f'Warning: quantities do not match ({num} :: {no1} :: {no2} :: {no3})')
                sto.append({'ID': idx, 'count': num, 'lev': lev, 'own': own})
                sum += num
        if len(sto) != count:
            print(f'Warning: count mismatch ({len(sto)} != {count}')
        return sto

    def edit(self, idx: int, add: int):
        aryx = self.data.find('.//array[@name="mStorageItem"]')
        ary = aryx.findall('./class[@type="sItemManager::cITEM_PARAM_DATA"]')
        free = None
        for a in ary:
            num = int(a.find('./s16[@name="data.mNum"]').get('value'))
            if num > 0:
                if idx == int(a.find('./s16[@name="data.mItemNo"]').get('value')):
                    n = num + add
                    if n > 0:
                        a.find('./s16[@name="data.mNum"]').set('value', str(n))
                        c = self.data.find('.//u32[@name="mStorageItemCount"]')
                        t = int(c.get('value')) + add
                        c.set('value', str(t))
                    else:
                        a.find('./s16[@name="data.mNum"]').set('value', str(0))
                        a.find('./s16[@name="data.mItemNo"]').set('value', str(-1))
                        a.find('./u32[@name="data.mFlag"]').set('value', str(0))
                        a.find('./u16[@name="data.mDay1"]').set('value', str(0))
                        a.find('./u16[@name="data.mDay2"]').set('value', str(0))
                        a.find('./u16[@name="data.mDay3"]').set('value', str(0))
                        a.find('./s8[@name="data.mOwnerId"]').set('value', str(0))
                        c = self.data.find('.//u32[@name="mStorageItemCount"]')
                        t = int(c.get('value')) - num
                        c.set('value', str(t))
                    self.storChanged.emit()
                    break
            elif free is None:
                free = a
        else:
            if add > 0:
                num = int(free.find('./s16[@name="data.mNum"]').get('value'))
                free.find('./s16[@name="data.mNum"]').set('value', str(add))
                free.find('./s16[@name="data.mItemNo"]').set('value', str(idx))
                free.find('./u32[@name="data.mFlag"]').set('value', str(0))
                free.find('./u16[@name="data.mDay1"]').set('value', str(0))
                free.find('./u16[@name="data.mDay2"]').set('value', str(0))
                free.find('./u16[@name="data.mDay3"]').set('value', str(0))
                free.find('./s8[@name="data.mOwnerId"]').set('value', str(4))
                c = self.data.find('.//u32[@name="mStorageItemCount"]')
                t = int(c.get('value')) + add + num
                c.set('value', str(t))
                self.storChanged.emit()


class ItemData:
    """
<array name="mItem" type="class" count="4">
<class type="cSAVE_DATA_ITEM">
<u32 name="mItemCount" value="#"/> - Number of Items in Inventory
<array name="mItem" type="class" count="256">
<class type="sItemManager::cITEM_PARAM_DATA">
<s16 name="data.mNum" value="#"/> - Item Quantity 1
<s16 name="data.mItemNo" value="#"/> - Item ID
<u32 name="data.mFlag" value="#"/> - Item Level/Tier - Tier ID list below
<u16 name="data.mChgNum" value="0"/> - UNKNOWN
<u16 name="data.mDay1" value="#"/> - Item Quantity 2 - 2, 3 and 4 HAVE to equal Item Quantity 1
<u16 name="data.mDay2" value="#"/> - Item Quantity 3 - 2, 3 and 4 HAVE to equal Item Quantity 1
<u16 name="data.mDay3" value="#"/> - Item Quantity 4 - 2, 3 and 4 HAVE to equal Item Quantity 1
<s8 name="data.mMutationPool" value="0"/> - UNKNOWN
<s8 name="data.mOwnerId" value="#"/> - Who the Item belongs to, 0= Main Character, 1= Main Pawn, etc.
<u32 name="data.mKey" value="0"/> - UNKNOWN
</class>
<class type="sItemManager::cITEM_PARAM_DATA"> - BLANK ITEM/NO ITEM
<s16 name="data.mNum" value="0"/>
<s16 name="data.mItemNo" value="-1"/>
<u32 name="data.mFlag" value="0"/>
<u16 name="data.mChgNum" value="0"/>
<u16 name="data.mDay1" value="0"/>
<u16 name="data.mDay2" value="0"/>
<u16 name="data.mDay3" value="0"/>
<s8 name="data.mMutationPool" value="0"/>
<s8 name="data.mOwnerId" value="0"/>
<u32 name="data.mKey" value="0"/>
</class>
    """

    def __init__(self, data: ET.Element):
        self.data = data.findall('.//array[@name="mItem"]/class[@type="cSAVE_DATA_ITEM"]')

    def get_pers_items(self, pers: int):
        data = self.data[pers].findall('./array/class[@type="sItemManager::cITEM_PARAM_DATA"]')
        ret = []
        for item in data:
            # ET.dump(item)
            m_num = int(item.find('./s16[@name="data.mNum"]').get('value'))
            m_item_no = int(item.find('./s16[@name="data.mItemNo"]').get('value'))
            if m_num > 0 and m_item_no >= 0:
                m_flag = int(item.find('./u32[@name="data.mFlag"]').get('value'))
                m_chg_num = int(item.find('./u16[@name="data.mChgNum"]').get('value'))
                m_day1 = int(item.find('./u16[@name="data.mDay1"]').get('value'))
                m_day2 = int(item.find('./u16[@name="data.mDay2"]').get('value'))
                m_day3 = int(item.find('./u16[@name="data.mDay3"]').get('value'))
                m_mutation_pool = int(item.find('./s8[@name="data.mMutationPool"]').get('value'))
                m_ownwr_id = int(item.find('./s8[@name="data.mOwnerId"]').get('value'))
                m_key = int(item.find('./u32[@name="data.mKey"]').get('value'))
                ret.append({
                    'num': m_num,
                    'item': all_by_id[m_item_no],
                    'flag': tier_by_id[m_flag]
                })
                if m_ownwr_id != pers:
                    print(f'{all_by_id[m_item_no]} -- {m_ownwr_id} != {pers}')
        return ret


if __name__ == '__main__':  # Test only
    dddafile = DDDAfile()
    dddafile.fname = '../DDsavetool/DDDA.sav'
    itemdata = ItemData(dddafile.data)
    pds = itemdata.get_pers_items(0)

    pprint.pprint(pds)
