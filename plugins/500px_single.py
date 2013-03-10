#Handles getting a single imgur image that isn't a direct link but rather a
# link to its imgur page

#works as of 02-23-13

import urllib
import urllib2
from lxml import etree


def get_500px_img(url):
    """Helper for the 500px execute function

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
    a = tree.findall('.//*[@id="thephoto"]/a')
    href = a[0].attrib['href']
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
            if cand['data']['url'].lower().startswith('http://500px.com/photo/'):
                img = get_500px_img(cand['data']['url'])
                to_acquire.append({'url': img,
                                   'subreddit': cand['data']['subreddit'],
                                   'title': cand['data']['title']})
                handled.append(cand)
        except Exception, e:
            exceptions.append((cand, e, '500px_single'))
    return handled, to_acquire, exceptions