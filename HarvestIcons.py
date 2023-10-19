from os import path, makedirs

import requests

import Armors
import Items
import Weapons

site = 'https://dragonsdogma.wiki.fextralife.com'
dest = 'resources/icons'


def harvest(dic):
    for item in dic.values():
        if item['img']:
            url = site + item['img']
            _, ext = path.splitext(url)
            n = item['Name'].replace("'", '')
            n = n.replace(' ', '_')
            fn = f"{item['tag']}-{n}{ext}"
            pn = path.join(dest, fn)
            if not path.exists(pn):
                print(fn)
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(pn, 'wb') as fo:
                        for chunk in r.iter_content(chunk_size=8192):
                            fo.write(chunk)
        else:
            print(f'Warning: no image for {item["Name"]}')


if __name__ == '__main__':
    if not path.isdir(dest):
        makedirs(dest)
    harvest(Armors.armors_by_name)
    harvest(Items.items_by_name)
    harvest(Weapons.weapons_by_name)
