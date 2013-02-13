#Handles getting all of the images from an album linked to on imgur

import urllib
import urllib2
from lxml import etree

def get_imgur_album(url):
    try:
        resp = urllib.urlopen(url)
    except urllib2.HTTPError, e:
        print 'Error contacting imgur (%s):' % url
        print e
        return []
    tree = etree.HTML(resp.read())
    urls = []
    for script in tree.findall('body/script'):
        if script.text is not None:
            if script.text.replace('\n','').lstrip().rstrip().startswith('var album'):
                album = eval(script.text.split('[', 1)[1].split(']',1)[0])
                #this check in case the album has one image, which returns dict instead of list
                if type(album) == list or type(album) == tuple:
                    for image in album:
                        url = 'http://i.imgur.com/%s%s' % (image['hash'], image['ext'])
                        urls.append(url)
                elif type(album) == dict:
                    url = 'http://i.imgur.com/%s%s' % (album['hash'], album['ext'])
                    urls.append(url)
                else:
                    print type(album), album
                    print 'Unhandled album type!'
                    raise ValueError

    return urls

def execute(children, candidates):
    handled = []
    for child in children:
        if child['data']['url'].lower().startswith('http://imgur.com/a/'):
            album_imgs = get_imgur_album(child['data']['url'])
            for album_img in album_imgs:
                candidates.append({'url' : album_img,
                                   'subreddit' : child['data']['subreddit'],
                                   'title' : child['data']['title']})
            handled.append(child)
    return handled, candidates