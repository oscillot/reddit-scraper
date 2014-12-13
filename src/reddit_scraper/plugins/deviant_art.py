import re

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import BasePlugin
from reddit_scraper.data_types import Download
from reddit_scraper.exceptions import PluginNeedsUpdated


class DeviantArt(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            deviant_art_img_url, deviant_art_cookie = self\
                .get_deviant_art_image(self.candidate.url)
            if deviant_art_img_url:
                if deviant_art_img_url == 'deviantART: 404 Not Found':
                    return
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        deviant_art_img_url,
                                        self.candidate.nsfw,
                                        deviant_art_cookie)
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
        This is matches all deviant art pages
        """
        if BasePlugin.get_basic_matcher('deviantart.com').match(url):
            return True
        else:
            return False

    @staticmethod
    def get_deviant_art_image(url):
        """Helper for the deviant art execute function

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """

        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except HTTPError, e:
            print 'Error contacting Deviantart (%s):' % url
            print '%s: %s\n' % (e.__class__.__name__, e)
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