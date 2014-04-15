import re
from bs4 import BeautifulSoup
from plugins.base_plugin import *


class Get500pxSingle(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            img_url = self.get_500px_img(self.candidate.url)
            self.current = Download(self.candidate.title,
                                    self.candidate.subreddit,
                                    img_url)

    @staticmethod
    def url_matches(url):
        """
        This matches 500px photo pages
        """

        px500_pat = re.compile(r'^http[s]?://.*500px\.com/photo/.*$',
                                 flags=re.IGNORECASE)
        if px500_pat.match(url):
            return True
        else:
            return False

    def get_500px_img(self, url):
        """Helper for the 500px execute function

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % url
            print e
            return []
        root = BeautifulSoup(resp.text)
        a = root.find(id='thephoto').find('a')
        return a.attrs.get('href')