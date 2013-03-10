#Handles getting all of the images from a collection linked to on wallbase.cc

#works as of 02-23-13

import urllib
import urllib2
from lxml import etree
import re
import base64
import time
from base_plugin import BasePlugin


class WallbaseCollection(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param dict candidate: data from a reddit post json
        """
        if candidate['data']['url'].lower().startswith('http://wallbase'
                                                       '.cc/user/collection/'):
            collection_imgs = self.get_wallbase_collection(candidate['data'][
                'url'])
            for img in collection_imgs:
                self.to_acquire.append({'url': img,
                                        'subreddit': candidate['data'][
                                            'subreddit'],
                                        'title': candidate['data']['title']})
            self.handled.append(candidate)

    def get_wallbase_collection(self, url):
        """Helper for the wallbase collection function. This will try to
        retirieve all of the pages of a collection and then stitch together a
        listing of all the different images from that collection.

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = urllib.urlopen(url)
        except urllib2.HTTPError, e:
            print 'Error contacting wallbase (%s):' % url
            print e
            return []
        tree = etree.HTML(resp.read())
        max_images = int(tree.find('.//*[@id="delwrap"]/div[1]/div[3]/span[1]').text)
        pages = []
        start = 1
        end = 32
        while end <= max_images + 64:  # for some reason everything is shifted
        #  by 32, plus we add an extra 32 for a full exceed above the required
            p = '%s%d/%d' % (url, start, end)
            pages.append(p)
            start += 32
            end += 32
        urls = []
        for i, p in enumerate(pages):
            thumb_links = []
            tree = etree.HTML(urllib.urlopen(p).read())
            t1 = time.time()
            for script in tree.findall('.//*[@class="thumb"]/a'):
                img_link = script.get('href')
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