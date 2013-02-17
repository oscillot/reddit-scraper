#Handles getting a single imgur image that isn't a direct link but rather a
# link to its imgur page

import urllib
import urllib2
from lxml import etree

def get_500px_img(url):
    try:
        resp = urllib.urlopen(url)
    except urllib2.HTTPError, e:
        print 'Error contacting imgur (%s):' % url
        print e
        return []
    tree = etree.HTML(resp.read())
    a = tree.findall('.//*[@id="thephoto"]/a')
    href = a.attrib['href']
    return href

def execute(children, candidates):
    handled = []
    for child in children:
        if child['data']['url'].lower().startswith('http://500px.com/'):
            img = get_500px_img(child['data']['url'])
            candidates.append({'url': img,
                               'subreddit': child['data']['subreddit'],
                               'title': child['data']['title']})
            handled.append(child)
    return handled, candidates