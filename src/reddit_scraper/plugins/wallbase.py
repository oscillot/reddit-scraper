#Handles getting all of the images from a collection linked to on wallbase.cc
import re
import base64

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import BasePlugin
from reddit_scraper.data_types import Download
from reddit_scraper.exceptions import PluginNeedsUpdated


class Wallbase(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            if self.is_coll(self.candidate.url):
                collection_imgs = self.get_wallbase_collection(self.candidate.url)
                if collection_imgs:
                    for img_url in collection_imgs:
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
            elif self.is_wall(self.candidate.url):
                img = self.get_wallbase_single(self.candidate.url)
                if img:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            img,
                                            self.candidate.nsfw)
                else:
                    #try to get an early warning next time this plugin stops working
                    try:
                        raise PluginNeedsUpdated(
                            'No image found from url: %s' % self.candidate.url)
                    except PluginNeedsUpdated, e:
                        print '%s: %s\n' % (e.__class__.__name__, e)
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
        This matches only wallbase user collections.
        """
        if BasePlugin.get_basic_matcher('wallbase.cc').match(url):
            return True
        else:
            return False

    @staticmethod
    def is_coll(url):
        """
        This matches only wallbase user collections.
        """

        wallbase_coll_pat = re.compile(r'^http[s]?://.*wallbase.cc/user/collection/.*$',
                                       flags=re.IGNORECASE)
        if wallbase_coll_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def is_wall(url):
        """
        This matches only wallbase user collections.
        """

        wallbase_coll_pat = re.compile(r'^http[s]?://.*wallbase.cc/wallpaper/[0-9]+$',
                                       flags=re.IGNORECASE)
        if wallbase_coll_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def get_wallbase_collection(url):
        """Helper for the wallbase collection function. This will try to
        retirieve all of the pages of a collection and then stitch together a
        listing of all the different images from that collection.

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(url)
        except HTTPError, e:
            print 'Error contacting wallbase (%s):' % url
            print e
            return []
        root = BeautifulSoup(resp.content)
        max_images = int(root.find({'id': 'delwrap'})
                             .find_all('div', recursive=False)[1]
                             .find_all('div', recursive=False)[3]
                             .find_all('span', recursive=False)[1].text)
        pages = []
        start = 1
        end = 32
        while end <= max_images + 64:  # for some reason everything is shifted
        #  by 32, plus we add an extra 32 for a full exceed above the required
            p = '%s%d/%d' % (url, start, end)
            pages.append(p)
            start += 32
            end += 32
        urls = []
        for i, p in enumerate(pages):
            thumb_links = []
            root = BeautifulSoup(requests.get(p).text)
            for script in root.find_all({'class': 'thumb'}, 'a'):
                img_link = script.attrs.get('href')
                thumb_links.append(img_link)
            for link in thumb_links:
                try:
                    resp = requests.get(link)
                except HTTPError, e:
                    print 'Error contacting wallbase (%s):' % url
                    print e
                    continue
                root = BeautifulSoup(resp.text)
                js = root.find(id='bigwall').find('script').text
                pat = re.compile(r'src="\'\+B\(\'[a-zA-Z0-9=\+\\]+\'\)\+\'"')
                match = re.search(pat, js)
                m = match.group().lstrip(r'src="\'\+B\(\'').rstrip(r'\'\)\+\'"')
                img_url = base64.b64decode(m)
                if img_url not in urls:
                    urls.append(img_url)
        return urls

    @staticmethod
    def get_wallbase_single(url):
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except HTTPError, e:
            print 'Error contacting Wallbase (%s):' % url
            print '%s: %s\n' % (e.__class__.__name__, e)
            return []
        root = BeautifulSoup(resp.content)
        img = root.find('img', attrs={'class': 'wall'})
        return img