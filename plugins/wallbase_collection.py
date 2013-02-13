#Handles getting all of the images from a collection linked to on wallbase.cc

import urllib
import urllib2
from lxml import etree
import re
import base64

def wget(url):
    resp = urllib.urlopen(url)
    return resp

def get_wallbase_collection(url):
    try:
        resp = wget(url)
    except urllib2.HTTPError, e:
        print 'Error contacting wallbase (%s):' % url
        print e
        return []
    tree = etree.HTML(resp.read())
    thumb_links = []
    max_images = int(tree.find('.//*[@id="delwrap"]/div[1]/div[3]/span[1]').text)
    pages = []
    start = 0
    end = 32
    while end <= max_images + 64: #for some reason everything is shifted by
    # 32, plus we add an extra 32 for a full exceed above the required
        pages.append('%s%d/%d' % (url, start, end))
        start += 32
        end += 32
    urls = []
    for p in pages:
        print p
        tree = etree.HTML(wget(p).read())
        for script in tree.findall('.//*[@class="thumb"]/a'):
            img_link = script.get('href')
            print img_link
            thumb_links.append(img_link)
        for link in thumb_links:
            try:
                resp = urllib.urlopen(link)
            except urllib2.HTTPError, e:
                print 'Error contacting wallbase (%s):' % url
                print e
                continue
            tree = etree.HTML(resp.read())
            js = tree.find('.//*[@id="bigwall"]/script').text
            pat = re.compile(r'src="\'\+B\(\'[a-zA-Z0-9=\+\\]+\'\)\+\'"')
            match = re.search(pat, js)
            m = match.group().lstrip(r'src="\'\+B\(\'').rstrip(r'\'\)\+\'"')
            img_url = base64.b64decode(m)
            if img_url not in urls:
                urls.append(img_url)
    return urls

def execute(children, candidates):
    handled = []
    for child in children:
        print child['data']['url']
        if child['data']['url'].lower().startswith('http://wallbase.cc/user/collection/'):
            collection_imgs = get_wallbase_collection(child['data']['url'])
            for img in collection_imgs:
                candidates.append({'url' : img,
                                   'subreddit' : child['data']['subreddit'],
                                   'title' : child['data']['title']})
            handled.append(child)
    return handled, candidates

# url = 'http://wallbase.cc/user/collection/80324/'
# urls = get_wallbase_collection(url)
# print len(urls), urls