import re
from bs4 import BeautifulSoup
from plugins.base_plugin import *


class DeviantArt(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches():
            deviant_art_img_url, deviant_art_cookie = self\
                .get_deviant_art_image(self.candidate.url)
            if deviant_art_img_url is not None:
                if deviant_art_img_url == 'deviantART: 404 Not Found':
                    return
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        deviant_art_img_url,
                                        deviant_art_cookie)

    @staticmethod
    def url_matches(self):
        """
        This is matches all deviant art pages
        """

        deviant_pat = re.compile(r'^http[s]?://.*deviantart\.com.*$',
                                 flags=re.IGNORECASE)
        if deviant_pat.match(self.candidate.url):
            return True
        else:
            return False

    def get_deviant_art_image(self, url):
        """Helper for the deviant art execute function

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """

        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error reaching deviantart (%s):' % url
            print e
            return
        root = BeautifulSoup(resp.text)

        for title in root.find_all('title'):
            if title.text == 'deviantART: 404 Not Found':
                print '%s: %s' % (url, title.text)
                return title.text, resp.cookies.get_dict()

        dl = root.find('meta', {'name': 'og:image'})
        if dl is not None:
            return dl.attrs.get('content'), resp.cookies.get_dict()

        for dl in root.find_all('a', ['dev-page-button',
                                      'dev-page-button-with-text',
                                      'dev-page-download']):
            if '/download/' in dl.attrs.get('href') and '?token' in \
                dl.attrs.get('href'):
                href = dl.attrs.get('href')
                #why do we split off the token here? let's turn that off
                # for now...
                # href = href.split('?token')[0]
                return href, resp.cookies.get_dict()

        for dl in root.find_all(id='download-button'):
            if '/download/' in dl.attrs.get('href'):
                return dl.attrs.get('href'), resp.cookies.get_dict()