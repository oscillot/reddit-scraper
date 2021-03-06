import re

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import BasePlugin
from reddit_scraper.data_types import Download
from reddit_scraper.exceptions import PluginNeedsUpdated


class Tumblr(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            img_urls = self.get_tumblr_imgs(self.candidate.url)
            if img_urls:
                for img_url in img_urls:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            img_url,
                                            self.candidate.nsfw)
            else:
                #try to get an early warning next time this plugin stops working
                try:
                    raise PluginNeedsUpdated(
                        'No images found from url: %s' % self.candidate.url)
                except PluginNeedsUpdated, e:
                    print '%s: %s\n' % (e.__class__.__name__, e)

    @staticmethod
    def url_matches(url):
        """
        This matches all tumblr urls
        """
        if BasePlugin.get_basic_matcher('tumblr.com').match(url):
            return True
        else:
            return False

    @staticmethod
    def get_tumblr_imgs(url):
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except HTTPError, e:
            print 'Error contacting tumblr (%s):' % url
            print e
            return []
        root = BeautifulSoup(resp.content)
        imgs = []

        metas = root.find_all('meta', {'property': 'og:image'})
        if metas:
            imgs.extend([m.attrs.get('content') for m in metas])
            return imgs
        else:
            for iframe in root.find_all('iframe', {'class': 'photoset'}):
                src = iframe.attrs.get('src')

                try:
                    resp = requests.get(src)
                    resp.raise_for_status()
                except HTTPError, e:
                    print 'Error contacting Tumblr (%s):' % url
                    print '%s: %s\n' % (e.__class__.__name__, e)
                    return []
                inner_root = BeautifulSoup(resp.text)

                for a in inner_root.find_all('a', {'class': 'photoset_photo'}):
                    imgs.append(a.attrs['href'])

            divs = root.find_all('div', {'class': 'photo-wrap'})
            if divs:
                for div in divs:
                    img = div.find('img')
                    imgs.append(img.attrs.get('src'))

        return imgs

# print Tumblr.get_tumblr_imgs('http://n6jlv.tumblr.com/post/83763121262/thanks-alan-you-are-an-amazing-photographer')
# print Tumblr.get_tumblr_imgs('http://afewvowels.tumblr.com/post/83723061060/ever-have-one-of-these-days')
