import re

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import Download, BasePlugin
from reddit_scraper.exceptions import PluginNeedsUpdated


class Behance(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            urls = Behance.get_behance_imgs(self.candidate.url)
            if urls:
                for url in urls:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            url,
                                            self.candidate.nsfw)
            else:
                #try to get an early warning next time this plugin stops working
                try:
                    raise PluginNeedsUpdated(
                        'No images found from gallery: %s' %
                        self.candidate.url)
                except PluginNeedsUpdated, e:
                    print '%s: %s\n' % (e.__class__.__name__, e)

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
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except HTTPError, e:
            print 'Error contacting Behance (%s):' % url
            print '%s: %s\n' % (e.__class__.__name__, e)
            return
        soup = BeautifulSoup(resp.content)

        ul = soup.find(id='project-modules')
        lis = ul.find_all('li')

        imgs = []
        for li in lis:
            img = li.find('img')
            imgs.append(img.attrs['data-hd-src'])

        return imgs