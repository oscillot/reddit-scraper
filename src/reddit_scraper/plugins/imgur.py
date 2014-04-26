#Handles getting all of the images from an album linked to on imgur
import json
import re

from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import *


class Imgur(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            img_urls = self.get_imgur_images(self.candidate.url)
            if img_urls:
                for img_url in img_urls:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            img_url,
                                            self.candidate.nsfw)
            else:
                #try to get an early warning next time this plugin stops working
                try:
                    raise ValueError('No image found from url: %s' %
                                     self.candidate.url)
                except ValueError, e:
                    print '%s: %s' % (e.__class__.__name__, e)

    @staticmethod
    def url_matches(url):
        """
        This matches all of imgur
        """

        imgur_alb_pat = re.compile(r'^http[s]?://.*imgur\.com.*$',
                                   flags=re.IGNORECASE)
        if imgur_alb_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def get_imgur_images(url):
        """Helper for the imgur single image page function

        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % url
            print e
            return []
        root = BeautifulSoup(resp.content)
        metas = root.find_all('meta', property='og:image')

        urls = []
        for meta in metas:
            urls.append(meta.attrs['content'])

        return urls

print Imgur.get_imgur_images('http://imgur.com/wtD08iT')