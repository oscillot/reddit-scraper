import requests
from lxml import etree

from plugins.base_plugin import *


class Tumblr(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param Download candidate: data from a reddit post json
        """
        if 'tumblr.com' in candidate.url.lower():
            img_urls = self.get_tumblr_imgs(candidate.url)
            for img_url in img_urls:
                self.current = Download(candidate.title,
                                        candidate.subreddit,
                                        img_url)

    def get_tumblr_imgs(self, url):
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting tumblr (%s):' % url
            print e
            return []
        tree = etree.HTML(resp.text)
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
            tree = etree.HTML(resp.text)

            for img in tree.findall('.//*[@class="photoset_photo"]'):
                imgs.append(img.attrib['href'])
        return imgs