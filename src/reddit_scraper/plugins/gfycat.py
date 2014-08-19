import re

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import BasePlugin
from reddit_scraper.data_types import Download
from reddit_scraper.exceptions import PluginNeedsUpdated


class GfyCat(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            url = GfyCat.get_gfycat_img(self.candidate.url)
            if url:
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        url,
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
        This matches a gfycat link
        """
        direct_pat = re.compile(r'^http[s]?://(?:www.)?gfycat\.com/'
                                r'(?:(?![.]{1}(?:' #that doesn't end with the extension
                                r'jpg|' #jpeg
                                r'jpeg|' #jpeg
                                r'gif|' #gif
                                r'bmp|' #bitmap
                                r'png)' #png
                                r').)*$',
                                flags=re.IGNORECASE)
        if direct_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def get_gfycat_img(url):
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except HTTPError, e:
            print 'Error contacting GfyCat (%s):' % url
            print '%s: %s\n' % (e.__class__.__name__, e)
            return
        soup = BeautifulSoup(resp.content)
        gif_link = soup.find(id='gifShareLink')
        return gif_link.text