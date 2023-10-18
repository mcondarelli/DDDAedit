import json
from os import path

import requests
from bs4 import BeautifulSoup
import pandas as pd

from ITEMS import item_ids


def scrap_curatives(url, tag):
    page = requests.get(url)
    text = page.text
    text = text.replace("</a></h4> </li> \n   <li><strong>", "</a></h4> <strong>")  # fix for site error
    soup = BeautifulSoup(text, 'lxml')
    sections = soup.find_all('ul', {'class': "searchable", 'data-key': "curatives"})
    tab = []
    for section in sections:
        for j in section.find_all('li'):
            pic = j.find('img')['data-src']
            nam = j.find('a').text
            dsc = "".join(j.find_all(string=True, recursive=False)).strip()
            dic = {'Name': nam.strip(), 'img': pic, 'tag': tag, 'effect': dsc}
            print(dic)
            tab.append(dic)
    return tab


def scrap_tools(url, tag):
    page = requests.get(url)
    text = page.text
    text = text.replace('  <br> \n', '')
    soup = BeautifulSoup(text, 'lxml')
    sections = soup.find_all('div', {'class': "col-sm-6"})
    tab = []
    for section in sections:
        '''
    <h4>
        <a class="wiki_link" title="Dragons Dogma Blast Arrow" href="/Blast+Arrow">
            <img class="lazyload" title="Dragon's Dogma Blast Arrow" src="/file/Monster-Hunter-World/thumbnails/mhws.png" alt="blast arrow items dragons dogma wiki guide" width="50" data-src="/file/Dragons-Dogma/blast-arrow-items-dragons-dogma-wiki-guide.png">
            Blast Arrow
        </a>
    </h4> 
    <p>
        <strong>
            Effect
        </strong>
        : Deals fire damage and inflicts 
        <a class="wiki_link" title="Dragons Dogma Burning" href="/Burning">
            Burning
        </a>
        , staggers foes.
    </p>         
        '''
        nam = pic = ''
        for j in section.find_all(recursive=False):
            if j.name == 'h4':
                nam = j.find('a').text
                try:
                    pic = j.find('img')['data-src']
                except TypeError:
                    pic = None
            elif j.name == 'p':
                dsc = j.text.strip()
                dic = {'Name': nam.strip(), 'img': pic, 'tag': tag, 'effect': dsc}
                print(dic)
                tab.append(dic)
            else:
                print(f'ERROR: unknown tag {j.name}')
    return tab


if __name__ == '__main__':
    tab = []
    t = scrap_curatives('https://dragonsdogma.wiki.fextralife.com/Curatives', 'curative')
    tab.extend(t)
    t = scrap_tools('https://dragonsdogma.wiki.fextralife.com/Arrows', 'arrow')
    tab.extend(t)
    t = scrap_tools('https://dragonsdogma.wiki.fextralife.com/Elixirs', 'elixir')
    tab.extend(t)
    t = scrap_tools('https://dragonsdogma.wiki.fextralife.com/Enemy+Strategy+Scrolls', 'strategy')
    tab.extend(t)
    t = scrap_tools('https://dragonsdogma.wiki.fextralife.com/Flasks', 'flask')
    tab.extend(t)
    t = scrap_tools('https://dragonsdogma.wiki.fextralife.com/Items+of+Use', 'useable')
    tab.extend(t)
    t = scrap_tools('https://dragonsdogma.wiki.fextralife.com/Navigation', 'navigation')
    tab.extend(t)
    t = scrap_tools('https://dragonsdogma.wiki.fextralife.com/Special+Tools', 'special')
    tab.extend(t)
    t = scrap_tools('https://dragonsdogma.wiki.fextralife.com/Thrown+Items', 'throwable')
    tab.extend(t)

    with open('Items.py', 'w') as fo:
        fo.write('_item = [')
        for w in tab:
            n = w['Name']
            if n not in ['Barrel', 'Boar', 'Box', 'Cracked Pot', 'Explosive Barrel', 'Indestructible Crate',
                         'Large Flask', 'Large Stone', 'Oil Pot', 'Poison Pot', 'Pot', 'Water Pot']:
                # The above are in site, can be hold, but don't seem to have a numeric ID and CANNOT be in inventory
                idx = item_ids[n]
                w['id'] = idx
                fo.write(f'            {w},\n')
        fo.write('           ]\n\n')
        fo.write('items_by_id = {x["id"]: x for x in _item}\n')
        fo.write('items_by_name = {x["Name"]: x for x in _item}\n')
