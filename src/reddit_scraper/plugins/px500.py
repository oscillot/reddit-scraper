import re

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import BasePlugin
from reddit_scraper.data_types import Download
from reddit_scraper.exceptions import PluginNeedsUpdated


class PX500(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            img_url = self.get_500px_img(self.candidate.url)
            if img_url:
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
        This matches 500px photo pages
        """
        px500_pat = re.compile(r'^http[s]?://.*500px\.com.*'
                               r'(?:(?![.]{1}(?:' #that doesn't end with the extension
                               r'jpg|' #jpeg
                               r'jpeg|' #jpeg
                               r'gif|' #gif
                               r'bmp|' #bitmap
                               r'png)' #png
                               r').)*$',
                               flags=re.IGNORECASE)
        if px500_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def is_image(url):
        """
        This matches 500px photo pages
        """
        px500_pat = re.compile(r'^http[s]?://.*500px\.com/photo/.*$',
                               flags=re.IGNORECASE)
        if px500_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def get_500px_img(url):
        """Helper for the 500px execute function

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except HTTPError, e:
            print 'Error contacting 500Px (%s):' % url
            print '%s: %s\n' % (e.__class__.__name__, e)
            return []
        root = BeautifulSoup(resp.text)
        img = root.find('div', attrs={'data-bind': 'photo_wrap'}).find('img')
        return img.attrs['src']

# print PX500.get_500px_img('http://500px.com/photo/13746291/shining-through-by-paul-rojas?utm_campaign=apr26_2PM_landscape_shiningthrough13746291&utm_medium=google&utm_source=500px')