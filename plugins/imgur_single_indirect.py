#Handles getting a single imgur image that isn't a direct link but rather a
# link to its imgur page

#works as of 02-23-13

import urllib
import urllib2
from lxml import etree

def get_imgur_single(url):
    """Helper for the imgur single image page function

    :param str url: a url to retrieve and execute the xpath on
    :rtype str: a url that is a direct link to an image
    """
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
            if (cand['data']['url'].lower().startswith('http://imgur.com/') and
                not cand['data']['url'].lower().startswith(
                'http://imgur.com/a/') and not cand['data']['url'].lower()[-4:]
                in ['.jpg', '.bmp', '.png', '.gif']) or \
                (cand['data']['url'].lower().startswith('http://i.imgur.com/')
                and not cand['data']['url'].lower()[-4:] in ['.jpg', '.bmp',
                                                              '.png', '.gif']):
                img = get_imgur_single(cand['data']['url'])
                #This handles the links that come down with extensions like
                # `jpg?1` that have been showing up lately. Regular links
                # should be unaffected by this. This is done here so that the
                #  list of handled links is still accurate.
                to_acquire.append({'url': img.split('?')[0],
                                   'subreddit': cand['data']['subreddit'],
                                   'title': cand['data']['title']})
                handled.append(cand)
        except Exception, e:
            exceptions.append((cand, e, 'imgur_single_indirect'))
    return handled, to_acquire, exceptions