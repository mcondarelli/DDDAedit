from PyQt6.QtGui import QStandardItemModel, QStandardItem

_vocations = {
    'Fighter':       {'ID': 1,
                      'icon':  'resources/DDicon_fighter.webp',
                      'primary': 'Swords',
                      'secondary': 'Shields'},
    'Strider':       {'ID': 2,
                      'icon':  'resources/DDicon_strider.webp',
                      'primary': 'Daggers',
                      'secondary': 'Shortbows'},
    'Mage':          {'ID': 3,
                      'icon':  'resources/DDicon_mage.webp',
                      'primary': 'Staves',
                      'secondary': 'None'},
    'Mystic Knight': {'ID': 4,
                      'icon':  'resources/DDicon_magicknight.webp',
                      'primary': ['Swords', 'Staves', 'Maces'],
                      'secondary': 'Magick Shields'},
    'Assassin':      {'ID': 5,
                      'icon':  'resources/DDicon_assassin.webp',
                      'primary': ['Swords', 'Daggers'],
                      'secondary': ['Shields', 'Shortbows']},
    'MagicK Archer': {'ID': 6,
                      'icon':  'resources/DDicon_magicarcher.webp',
                      'primary': ['Staves', 'Daggers'],
                      'secondary': 'Magick Bows'},
    'Warrior':       {'ID': 7,
                      'icon':  'resources/DDicon_warrior.webp',
                      'primary': ['Longswords', 'Warhammers'],
                      'secondary': 'Shields'},
    'Ranger':        {'ID': 8,
                      'icon':  'resources/DDicon_ranger.webp',
                      'primary': 'Daggers',
                      'secondary': 'Longbows'},
    'Sorcerer':      {'ID': 9,
                      'icon':  'resources/DDicon_sorcerer.webp',
                      'primary': 'Archistaves',
                      'secondary': 'None'}
}

_voc_by_id = {v['ID']: v | {'Name': k} for k, v in _vocations.items()}


def name(x):
    return x if isinstance(x, str) else _voc_by_id[x]['Name']


def icon(x):
    return _voc_by_id[x]['icon'] if isinstance(x, int) else _vocations[x]['icon']


def primary(x):
    return _voc_by_id[x]['primary'] if isinstance(x, int) else _vocations[x]['primary']


def secondary(x):
    return _voc_by_id[x]['secondary'] if isinstance(x, int) else _vocations[x]['secondary']


class VocationsModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        for v in _vocations:
            item = QStandardItem(v)
            item.setData(_voc_by_id[_vocations[v]['ID']])
            self.invisibleRootItem().appendRow(item)


def vocations():
    for v in _vocations:
        yield v
