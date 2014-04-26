import re
import requests

from reddit_scraper.plugins.base_plugin import *


class Flickr(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            #This just throws us back in case the link we have is for a
            # pre-selected size, so we can choose high quality like normal
            if '/sizes/' in self.candidate.url:
                self.candidate.url = self.candidate.url.split('/sizes/')[0]
            flickr_img_url = self.get_best_quality(self.candidate.url)
            if flickr_img_url:
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        flickr_img_url,
                                        self.candidate.nsfw)
            else:
                #try to get an early warning next time this plugin stops working
                try:
                    raise ValueError('No image found from url: %s' %
                                     self.candidate.url)
                except ValueError, e:
                    print '%s: %s' % (e.__class__.__name__, e)

    @staticmethod
    def url_matches(url):
        """
        This matches flickr photo pages
        """

        flickr_pat = re.compile(r'^http[s]?://.*www\.flickr\.com/photos/'
                                r'(?:(?![.]{1}(?:' #that doesn't end with the extension
                                r'jpg|' #jpeg
                                r'jpeg|' #jpeg
                                r'gif|' #gif
                                r'bmp|' #bitmap
                                r'png)' #png
                                r').)*$',
                                flags=re.IGNORECASE)
        if flickr_pat.match(url):
            return True
        else:
            return False

    def get_best_quality(self, url):
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error reaching Flickr (%s)' % url
            print e
            return
        page = resp.text
        find_qualities = re.compile(r'Y.photo.init\((.+)\)', re.MULTILINE)
        match = re.search(find_qualities, page)
        #some ugly de-jsification hackery here
        qualities = eval(match.group(1).replace(
            'true', 'True').replace('false', 'False').replace('null', 'None'))
        if type(qualities) != dict:
            raise ValueError('Did not resolve to a dict. That\'s really '
                             '*really* bad! You got a: %s' % type(qualities))
        sizes = qualities['sizes']
        sizemore = {}
        areas = []
        for size in sizes.keys():
            #whatever has the largest area must be the biggest
            area = int(sizes[size]['width']) * int(sizes[size]['height'])
            areas.append(area)
            sizemore[area] = sizes[size]['url'].replace('\\', '')

        areas = sorted(areas, reverse=True)
        try:
            #ipso facto
            largest = areas[0]
            return sizemore[largest]
        except IndexError:
            return None