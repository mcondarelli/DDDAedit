import pprint
import struct
import zlib
from typing import Optional

from PyQt6.QtCore import QObject, pyqtProperty, Qt, pyqtSignal
from PyQt6.QtGui import QCursor

import xml.etree.ElementTree as ET

from PyQt6.QtWidgets import QWidget

from ITEMS import items_by_name, items_by_id

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
                    'item': items_by_id[m_item_no],
                    'flag': tier_by_id[m_flag]
                })
                if m_ownwr_id != pers:
                    print(f'{items_by_id[m_item_no]} -- {m_ownwr_id} != {pers}')
        return ret


if __name__ == '__main__':  # Test only
    dddafile = DDDAfile()
    dddafile.fname = '../DDsavetool/DDDA.sav'
    itemdata = ItemData(dddafile.data)
    pds = itemdata.get_pers_items(0)

    pprint.pprint(pds)
