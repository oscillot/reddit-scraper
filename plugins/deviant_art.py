#Handles getting the image url from the download button of a single image on deviant art

import urllib
import urllib2
from lxml import etree

def get_deviant_art_image(url):
    try:
        resp = urllib.urlopen(url)
    except urllib2.HTTPError, e:
        print 'Error reaching deviantart (%s):' % url
        print e
        return
    tree = etree.HTML(resp.read())
    for dl in tree.findall('.//*[@id="download-button"]'):
        if '/download/' in dl.attrib['href']:
            return dl.attrib['href']

def execute(children, candidates):
    handled = []
    for child in children:
        if 'deviantart.com' in child['data']['url'].lower():
            deviant_art_img = get_deviant_art_image(child['data']['url'])
            if deviant_art_img is not None:
                candidates.append({'url' : deviant_art_img,
                                   'subreddit' : child['data']['subreddit'],
                                   'title' : child['data']['title']})
                handled.append(child)
    return handled, candidates