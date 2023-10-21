import json
import os
from os import path

import requests
from bs4 import BeautifulSoup

from ITEMS import item_ids, id_to_item

site = 'https://dragonsdogma.fandom.com'
idir = 'resources/images'


def slurp(url, dst):
    if not path.exists(dst):
        print(dst)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dst, 'wb') as fo:
                for chunk in r.iter_content(chunk_size=8192):
                    fo.write(chunk)


def scrape_item(url, dest, idx=-1):
    with requests.get(url) as page:
        page.raise_for_status()
        soup = BeautifulSoup(page.text, 'lxml')
    aside = soup.find('aside', {'role': 'region'})
    imgu = aside.find('a')['href']
    ext = path.splitext(aside.find('img')["data-image-name"])[1]
    slurp(imgu, dest+ext)
    name = aside.find('h2', {'data-source': 'name'}).text
    typ = aside.find('div', {'data-source': 'type'}).find('a').text
    desc = soup.find('meta', {'property': "og:description"})
    if idx < 0:
        return dest+ext, desc['content'].strip()

    return {'ID': idx, 'Name': name, 'Type': typ, 'img': dest+ext, 'desc': desc['content'].strip()}


def scrape_items():
    url = site + '/wiki/List_of_Items'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    table = soup.find('table', {'class': "sortable"})
    tab = []
    headers = []
    for i in table.find_all('th'):
        title = i.text.strip()
        headers.append(title)
    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')
        row = [i.text.strip() for i in row_data]
        dic = {headers[i]: row[i] for i in range(len(headers))}
        try:
            sub_page = row_data[1].find('a')['href']
            if sub_page:
                i, d = scrape_item(site + sub_page, path.join(idir, dic["Name"]))
                dic['img'] = i
                dic['desc'] = d
        except TypeError:
            pass
        tab.append(dic)
    return tab


def scrape_weapon(url, typ):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    table = soup.find('table', {'class': "sortable"})
    tab = []
    headers = []
    rows = table.find_all('tr')
    for i in rows[0].find_all('th'):
        title = i.text.strip()
        headers.append(title)
    for j in rows[1:]:
        row_data = j.find_all(recursive=False)
        row = [i.text.strip() for i in row_data]
        dic = {headers[i]: row[i] for i in range(len(headers))}
        try:
            sub_page = row_data[0].find('a')['href']
            if sub_page:
                i, d = scrape_item(site + sub_page, path.join(idir, dic["Name"]))
                dic['img'] = i
                dic['desc'] = d
        except TypeError:
            pass
        match row_data[0]['class']:
            case 'txtbg1':
                dic['release'] = 'DD'
            case 'txtbg2':
                dic['release'] = 'DLC'
            case 'txtbg3':
                dic['release'] = 'DDDA'
        dic['Type'] = typ

        tab.append(dic)
    return tab


def scrape_weapons():
    allw = []
    allw.extend(scrape_weapon(site + '/wiki/Category:Archistaves', 'Archistaff'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Daggers', 'Dagger'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Longbows', 'Longbow'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Longswords', 'Longsword'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Maces', 'Mace'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Magick_Bows', 'Magick Bow'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Magick_Shields', 'Magick Shield'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Shields', 'Shield'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Shortbows', 'Shortbow'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Staves', 'Staff'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Swords', 'Sword'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Warhammers', 'Warhammer'))
    return allw


def parse_resist(data):
    res = {}
    for r in data.find_all('tr'):
        try:
            t = r.find('a')['title']
            v = r.find('td').text.strip()
            res[t] = v
        except TypeError:
            pass
    return res


def scrape_armor(url, typ):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    table = soup.find('table', {'class': "sortable"})
    tab = []
    headers = []
    rows = table.find('tbody').find_all('tr', recursive=False)
    for i in rows[0].find_all('th'):
        title = i.text.strip()
        headers.append(title)
    for j in rows[1:]:
        row_data = j.find_all(recursive=False)
        row = [i.text.strip() for i in row_data]
        dic = {headers[i]: row[i] for i in range(len(headers))}
        try:
            sub_page = row_data[0].find('a')['href']
            if sub_page:
                i, d = scrape_item(site + sub_page, path.join(idir, dic["Name"]))
                dic['img'] = i
                dic['desc'] = d
        except TypeError:
            pass
        er = dr = None
        if headers[7] == 'ElementalResist':
            dic['ElementalResist'] = parse_resist(row_data[7])
        if headers[8] == 'DebilitationResist':
            dic['DebilitationResist'] = parse_resist(row_data[7])
        dic['Type'] = typ

        tab.append(dic)
    return tab


def scrape_armors():
    allw = []
    allw.extend(scrape_armor(site + '/wiki/List_of_Arms_Armor', 'Arms Armor'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Cloaks', 'Cloak'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Head_Armor', 'Head Armor'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Leg_Armor', 'Leg Armor'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Leg_Clothing', 'Leg Clothing'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Chest_Clothing', 'Chest Clothing'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Head_Armor', 'Head Armor'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Torso_Armor', 'Torso Armor'))
    return allw


def backcheck(tab):
    all_by_id = {x["ID"]: x for x in tab}
    changed = False

    def try_url(url, img, idx):
        try:
            return scrape_item(url, img, idx)
        except AttributeError:
            print(f'ERROR: page found but scrape failed ({url})')
            return {'ID': i, 'Name': n, 'Type': 'malformed', 'img': None, 'desc': url}
        except requests.HTTPError as e:
            return None
        except:
            return None

    for i in range(item_ids['Used']):
        try:
            print(f'{i:04d} - {all_by_id[i]["Name"]}', end='\r')
        except KeyError:
            n = id_to_item[i]
            if n != 'Unknown Item':
                print(f'ERROR: index {i} not found ({n})')
                url = f'{site}/wiki/{n.replace(" ", "_")}'
                d = try_url(url, path.join(idir, n), i)
                if d is None:
                    match n.split():
                        case ['Small', *tail] | ['Large', *tail] | ['Huge', *tail] | ['Giant', *tail]:
                            d = try_url(f'{site}/wiki/{"_".join(tail)}', path.join(idir, n), i)
                        case [*head, 'Forgery']:
                            d = try_url(f'{site}/wiki/{"_".join(head)}', path.join(idir, n), i)
                    if d is None:
                        d = {'ID': i, 'Name': n, 'Type': 'Unknown', 'img': None,
                             'desc': 'This item was not found in "dragonsdogma.fandom.com'}
                print(d)
                tab.append(d)
                changed = True

    return changed


if __name__ == '__main__':
    if not path.isdir(idir):
        os.makedirs(idir)
    if path.isfile('fandom_tab.json'):
        with open('fandom_tab.json') as fi:
            tab = json.load(fi)
    else:
        tab = []
        tab.extend(scrape_items())
        tab.extend(scrape_weapons())
        tab.extend(scrape_armors())
        with open('fandom_tab.json', 'w') as fo:
            json.dump(tab, fo)
    for w in tab:
        n = w['Name']
        idx = item_ids[n]
        w['ID'] = idx

    if backcheck(tab):
        with open('fandom_tab.json', 'w') as fo:
            json.dump(tab, fo)

    with open('Fandom.py', 'w') as fo:
        fo.write('_all_items = [\n')
        for w in tab:
            n = w['Name']
            idx = item_ids[n]
            w['id'] = idx
            fo.write(f'    {w},\n')
        fo.write('    ]\n')
        fo.write('all_by_id = {x["ID"]: x for x in _all_items}\n')
        fo.write('all_by_name = {x["Name"]: x for x in _all_items}\n')
