#worked for 1 link 3/10/13 - still experimental

from base_plugin import BasePlugin
import requests
from lxml import etree

class Tumblr(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param dict candidate: data from a reddit post json
        """
        if 'tumblr.com' in candidate['data']['url'].lower():
            imgs = self.get_tumblr_imgs(candidate['data']['url'])
            for img in imgs:
                self.to_acquire.append({'url': img,
                    'subreddit': candidate['data']['subreddit'],
                    'title': candidate['data']['title']})
            self.handled.append(candidate)

    def get_tumblr_imgs(self, url):
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting tumblr (%s):' % url
            print e
            return []
        tree = etree.HTML(resp.read())
        urls = []
        imgs = []

        for iframe in tree.findall('.//*/iframe[@class="photoset"]'):
            src = iframe.attrib['src']

            try:
                resp = requests.get(src)
            except requests.HTTPError, e:
                print 'Error contacting tumblr (%s):' % url
                print e
                return []
            tree = etree.HTML(resp.read())

            for img in tree.findall('.//*[@class="photoset_photo"]'):
                imgs.append(img.attrib['href'])
        return imgs