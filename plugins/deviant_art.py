#Handles getting the image url from the download button of a single image on deviant art

import urllib
from lxml import etree

def get_deviant_art_image(url):
    resp = urllib.urlopen(url)
    tree = etree.HTML(resp.read())
    for dl in tree.findall('.//*[@id="download-button"]'):
        if '/download/' in dl.attrib['href']:
            return dl.attrib['href']

def execute(children, candidates):
    handled = []
    for child in children:
        if 'deviantart.com' in child['data']['url'].lower():
            deviant_art_img = get_deviant_art_image(child['data']['url'])
            if deviant_art_img != None:
                candidates.append({'url' : deviant_art_img,
                                   'subreddit' : child['data']['subreddit'],
                                   'title' : child['data']['title']})
                handled.append(child)
    return handled, candidates