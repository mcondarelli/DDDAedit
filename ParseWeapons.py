import json
from os import path

import requests
from bs4 import BeautifulSoup
import pandas as pd

from ITEMS import item_ids

site = 'https://dragonsdogma.wiki.fextralife.com'
pages = [
    {'page': "/Archistaves", 'tag': 'astaff'},
    {'page': "/Daggers", 'tag': 'dagger'},
    {'page': "/Longbows", 'tag': 'lbow'},
    {'page': "/Longswords", 'tag': 'lsword'},
    {'page': "/Maces", 'tag': 'mace'},
    {'page': "/Magick+Bows", 'tag': 'mbow'},
    {'page': "/Magick+Shields", 'tag': 'mshield'},
    {'page': "/Shields", 'tag': 'shield'},
    {'page': "/Shortbows", 'tag': 'sbow'},
    {'page': "/Staves", 'tag': 'staff'},
    {'page': "/Swords", 'tag': 'swoed'},
    {'page': "/Warhammers", 'tag': 'hammer'},
]


def scrape(url, tag):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    table = soup.find('table', {'class': "wiki_table sortable searchable"})
    print(url, tag, table)
    tab = []
    headers = []
    for i in table.find_all('th'):
        title = i.text
        headers.append(title)
    headers.append('img')
    headers.append('tag')
    data = pd.DataFrame(columns=headers)
    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')
        row = [i.text for i in row_data]
        try:
            row.append(row_data[0].find('img')['data-src'])
        except TypeError:
            row.append('')
        row.append(tag)
        length = len(data)
        data.loc[length] = row
        dic = {headers[i]: row[i] for i in range(len(headers))}
        dic['deab'] = [x['alt'].split()[0] for x in row_data[8].find_all('img')]
        dic['Name'] = dic['Name'].strip()

        if dic['Name'].endswith('*'):
            dic['Name'] = dic['Name'][:-1]
            dic['DDDAonly'] = True
        else:
            dic['DDDAonly'] = False
        tab.append(dic)
    return tab


if __name__ == '__main__':
    tab = []
    if path.exists('tab.json'):
        with open('tab.json') as fi:
            tab = json.load(fi)
    else:
        for p in pages:
            t = scrape(site + p['page'], p['tag'])
            tab.extend(t)
        with open('tab.json', 'w') as fo:
            json.dump(tab, fo, indent=4)

    with open('Weapons.py', 'w') as fo:
        fo.write('weapons = [')
        for w in tab:
            n = w['Name']
            idx = item_ids[n]
            w['id'] = idx
            fo.write(f'           {w},\n')
        fo.write('          ]\n')
