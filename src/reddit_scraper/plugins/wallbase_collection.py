#Handles getting all of the images from a collection linked to on wallbase.cc

#works as of 02-23-13

import re
import base64

from bs4 import BeautifulSoup

from src.reddit_scraper.plugins.base_plugin import *


class WallbaseCollection(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            collection_imgs = self.get_wallbase_collection(self.candidate.url)
            for img_url in collection_imgs:
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        img_url,
                                        self.candidate.nsfw)

    @staticmethod
    def url_matches(url):
        """
        This matches only wallbase user collections.
        """

        wallbase_coll_pat = re.compile(r'^http[s]?://.*wallbase.cc/user/collection/.*$',
                                       flags=re.IGNORECASE)
        if wallbase_coll_pat.match(url):
            return True
        else:
            return False

    def get_wallbase_collection(self, url):
        """Helper for the wallbase collection function. This will try to
        retirieve all of the pages of a collection and then stitch together a
        listing of all the different images from that collection.

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting wallbase (%s):' % url
            print e
            return []
        root = BeautifulSoup(resp.text)
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
                except requests.HTTPError, e:
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