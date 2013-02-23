#Handles getting a single imgur image that isn't a direct link but rather a
# link to its imgur page

#works as of 02-23-13

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
    href = a[0].attrib['href']
    return href


def execute(candidates, to_acquire):
    handled = []
    for child in candidates:
        if child['data']['url'].lower().startswith('http://500px.com/photo/'):
            img = get_500px_img(child['data']['url'])
            to_acquire.append({'url': img,
                               'subreddit': child['data']['subreddit'],
                               'title': child['data']['title']})
            handled.append(child)
    return handled, to_acquire