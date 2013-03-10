#Handles getting all of the images from an album linked to on imgur

#works as of 02-23-13

import urllib
import urllib2
from lxml import etree


def get_imgur_album(url):
    """Helper for the imgur album execute function

    :param str url: a url to retrieve and execute the xpath on
    :rtype list: a list of urls that is are direct links to images
    """
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
                album = eval('[{%s}]' % script.text.split('[{')[1].split('}]')[
                    0])
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

def execute(candidates, to_acquire):
    """Executor for this plugin. The entry function by which any plugin must
    operate to handle links.

    :param list candidates: a list of dictionaries converted from the json
    response given back by reddit.
    :rtype list, list: a list of the dictionary data that was successfully
    parsed by this plugin, a list of dictionaries with the url,
    subreddit and title of the direct link for later acquisition and database
     entry
    """
    handled = []
    exceptions = []
    for cand in candidates:
        try:
            if cand['data']['url'].lower().startswith('http://imgur.com/a/'):
                album_imgs = get_imgur_album(cand['data']['url'])
                for album_img in album_imgs:
                    #This handles the links that come down with extensions like
                    # `jpg?1` that have been showing up lately. Regular links
                    # should be unaffected by this. This is done here so that the
                    #  list of handled links is still accurate.
                    to_acquire.append({'url' : album_img.split('?')[0],
                                       'subreddit' : cand['data']['subreddit'],
                                       'title' : cand['data']['title']})
                handled.append(cand)
        except Exception, e:
            exceptions.append((cand, e, 'imgur_albums'))
    return handled, to_acquire, exceptions