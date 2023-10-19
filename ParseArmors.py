import json
from os import path

import requests
from bs4 import BeautifulSoup
import pandas as pd

from ITEMS import item_ids


def scrape(url, tag):
    page = requests.get(url)
    text = page.text
    text = text.replace('&nbsp;', '')
    soup = BeautifulSoup(text, 'lxml')
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
            i = row_data[0].find('img')
            try:
                f = i['data-src']
            except KeyError:
                # this is to fix is few errors in the site (Leather Circlet)
                try:
                    f = i['src']
                except KeyError:
                    f = None
            row.append(f)
        except TypeError:
            row.append('')
        row.append(tag)
        length = len(data)
        data.loc[length] = row
        dic = {headers[i]: row[i] for i in range(len(headers))}
        if len(dic['Elemental Res'].strip()) < 2:
            dic['Elemental Res'] = {}
        else:
            eres = {}
            el = row_data[7].find_all('img')
            enl = []
            for x in range(len(el)):
                e = el[x]['alt'].split()
                en = e[0] if e[0] != 'negative' else e[1]
                enl.append(en)
            erl = [f'{x.strip()}%' for x in dic['Elemental Res'].split('%') if x.strip()]
            if len(enl) != len(erl):
                print(f'ERROR: Elem {len(enl)} != {len(erl)}')
            else:
                eres = {enl[x]: erl[x] for x in range(len(enl))}
            dic['Elemental Res'] = eres
        if len(dic['Debilitation Res'].strip()) < 2:
            dic['Debilitation Res'] = {}
        else:
            dres = {}
            dl = row_data[8].find_all('img')
            dnl = []
            for x in range(len(dl)):
                d = dl[x]['alt'].split()
                dn = d[0] if d[0] != 'negative' else d[1]
                dnl.append(dn)
            drl = [f'{x.strip()}%' for x in dic['Debilitation Res'].split('%') if x.strip()]
            if len(dnl) != len(drl):
                print(f'ERROR: Deab {len(dnl)} != {len(drl)}')
            else:
                dres = {dnl[x]: drl[x] for x in range(len(dnl))}
            dic['Debilitation Res'] = dres
        dic['Name'] = dic['Name'].strip()

        tab.append(dic)
    return tab


if __name__ == '__main__':
    tab = []
    t = scrape('https://dragonsdogma.wiki.fextralife.com/Head+Armor', 'head')
    tab.extend(t)
    t = scrape('https://dragonsdogma.wiki.fextralife.com/Torso+Armor', 'chest')
    tab.extend(t)
    t = scrape('https://dragonsdogma.wiki.fextralife.com/Arm+Armor', 'arms')
    tab.extend(t)
    t = scrape('https://dragonsdogma.wiki.fextralife.com/Leg+Armor', 'legs')
    tab.extend(t)
    t = scrape('https://dragonsdogma.wiki.fextralife.com/Outfits', 'full')
    tab.extend(t)
    t = scrape('https://dragonsdogma.wiki.fextralife.com/Cloaks', 'cloak')
    tab.extend(t)

    with open('Armors.py', 'w') as fo:
        fo.write('_armors = [')
        for w in tab:
            n = w['Name']
            idx = item_ids[n]
            w['id'] = idx
            fo.write(f'           {w},\n')
        fo.write('          ]\n')
        fo.write('armors_by_id = {x["id"]: x for x in _armors}\n')
        fo.write('armors_by_name = {x["Name"]: x for x in _armors}\n')
