#Handles getting all of the images from an album linked to on imgur
import re

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import BasePlugin
from reddit_scraper.data_types import Download
from reddit_scraper.exceptions import PluginNeedsUpdated


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
                    raise PluginNeedsUpdated(
                        'No image found from url: %s' % self.candidate.url)
                except PluginNeedsUpdated, e:
                    print '%s: %s\n' % (e.__class__.__name__, e)

    @staticmethod
    def url_matches(url):
        """
        This matches all of imgur
        """
        if BasePlugin.get_basic_matcher('imgur.com').match(url):
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
            resp.raise_for_status()
        except HTTPError, e:
            print 'Error contacting Imgur (%s):' % url
            print '%s: %s\n' % (e.__class__.__name__, e)
            return []
        root = BeautifulSoup(resp.content)
        metas = root.find_all('meta', property='og:image')

        urls = []
        for meta in metas:
            urls.append(meta.attrs['content'])

        return urls