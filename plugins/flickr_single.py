import re

from plugins.base_plugin import *


class FlickrSingle(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches():
            #This just throws us back in case the link we have is for a
            # pre-selected size, so we can choose high quality like normal
            if '/sizes/' in self.candidate.url:
                self.candidate.url = self.candidate.url.split('/sizes/')[0]
            flickr_img_url = self.get_best_quality(self.candidate.url)
            if flickr_img_url is not None:
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        flickr_img_url)

    @staticmethod
    def url_matches(self):
        """
        This matches flickr photo pages
        """

        flickr_pat = re.compile(r'^http[s]?://.*www\.flickr\.com/photos/.*$',
                                flags=re.IGNORECASE)
        if flickr_pat.match(self.candidate.url):
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