#Handles getting the image url from the download button of a single image on
# deviant art

#works as of 02-23-13

import urllib
import urllib2
from lxml import etree


def get_deviant_art_image(url):
    """Helper for the deviant art execute function

    :param str url: a url to retrieve and execute the xpath on
    :rtype str: a url that is a direct link to an image
    """

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
    dl = tree.find('.//*/meta[@name="og:image"]')
    if dl is not None:
        return dl.attrib['content']


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
            if 'deviantart.com' in cand['data']['url'].lower():
                deviant_art_img = get_deviant_art_image(cand['data']['url'])
                if deviant_art_img is not None:
                    to_acquire.append({'url' : deviant_art_img,
                                       'subreddit' : cand['data']['subreddit'],
                                       'title' : cand['data']['title']})
                    handled.append(cand)
        except Exception, e:
            exceptions.append((cand, e, 'deviant_art'))
    return handled, to_acquire, exceptions