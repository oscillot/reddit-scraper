import re
import requests
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import *


class Behance(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            urls = Behance.get_behance_imgs(self.candidate.url)
            for url in urls:
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        url,
                                        self.candidate.nsfw)

    @staticmethod
    def url_matches(url):
        """
        This matches a gfycat link
        """
        direct_pat = re.compile(r'^http[s]?://www\.behance\.net/gallery/.*$',
                                flags=re.IGNORECASE)
        if direct_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def get_behance_imgs(url):
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content)

        ul = soup.find(id='project-modules')
        lis = ul.find_all('li')

        imgs = []
        for li in lis:
            img = li.find('img')
            imgs.append(img.attrs['data-hd-src'])

        if not imgs:
            #try to get an early warning next time this plugin stops working
            try:
                raise ValueError('No image found from url: %s' % url)
            except ValueError:
                pass

        return imgs