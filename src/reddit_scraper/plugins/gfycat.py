import re
import requests
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import *


class GfyCat(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            url = GfyCat.get_gfycat_img(self.candidate.url)
            self.current = Download(self.candidate.title,
                                    self.candidate.subreddit,
                                    url,
                                    self.candidate.nsfw)

    @staticmethod
    def url_matches(url):
        """
        This matches a gfycat link
        """
        direct_pat = re.compile(r'^http[s]?://gfycat\.com/.*$',
                                flags=re.IGNORECASE)
        if direct_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def get_gfycat_img(url):
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content)
        gif_link = soup.find(id='gifShareLink')
        if not gif_link:
                #try to get an early warning next time this plugin stops working
            try:
                raise ValueError('No image found from url: %s' % url)
            except ValueError:
                pass
        return gif_link.text