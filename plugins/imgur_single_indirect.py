#Handles getting a single imgur image that isn't a direct link but rather a
# link to its imgur page

import urllib
import urllib2
from lxml import etree

def get_imgur_single(url):
    try:
        resp = urllib.urlopen(url)
    except urllib2.HTTPError, e:
        print 'Error contacting imgur (%s):' % url
        print e
        return []
    tree = etree.HTML(resp.read())
    al = tree.findall('.//head/link')
    for a in al:
        href = a.attrib['href']
        if url.lstrip('http://') in href:
            return href

def execute(children, candidates):
    handled = []
    for child in children:
        if (child['data']['url'].lower().startswith('http://imgur.com/') and
            not child['data']['url'].lower().startswith(
            'http://imgur.com/a/') and not child['data']['url'].lower()[-4:]
            in ['.jpg', '.bmp', '.png', '.gif']) or \
            (child['data']['url'].lower().startswith('http://i.imgur.com/')
            and not child['data']['url'].lower()[-4:] in ['.jpg', '.bmp',
                                                          '.png', '.gif']):
            img = get_imgur_single(child['data']['url'])
            #This handles the links that come down with extensions like
            # `jpg?1` that have been showing up lately. Regular links
            # should be unaffected by this. This is done here so that the
            #  list of handled links is still accurate.
            candidates.append({'url': img.split('?')[0],
                               'subreddit': child['data']['subreddit'],
                               'title': child['data']['title']})
            handled.append(child)
    return handled, candidates