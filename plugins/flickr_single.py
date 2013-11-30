import re
import requests

from plugins.base_plugin import *


class FlickrSingle(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param Download candidate: data from a reddit post json
        """
        if 'www.flickr.com/photos/' in candidate.url:
            #This just throws us back in case the link we have is for a
            # pre-selected size, so we can choose high quality like normal
            if '/sizes/' in candidate.url:
                candidate.url = candidate.url.split('/sizes/')[0]
            flickr_img_url = self.get_best_quality(candidate.url)
            if flickr_img_url is not None:
                self.current = Download(candidate.title,
                                        candidate.subreddit,
                                        flickr_img_url)

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