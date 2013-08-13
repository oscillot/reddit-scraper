#works as of 08-13-13
import re
import urllib
import urllib2

from base_plugin import BasePlugin


class FlickrSingle(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param dict candidate: data from a reddit post json
        """
        if 'www.flickr.com/photos/' in candidate['data']['url']:
            flickr_img = self.get_best_quality(candidate['data']['url'])
            if flickr_img is not None:
                self.to_acquire.append({'url': flickr_img,
                                        'subreddit': candidate['data'][
                                            'subreddit'],
                                        'title': candidate['data']['title']})
                self.handled.append(candidate)

    def get_best_quality(self, url):
        try:
            resp = urllib.urlopen(url)
        except urllib2.HTTPError, e:
            print 'Error reaching Flickr (%s)' % url
            print e
            return
        page = resp.read().replace('true', 'True').replace('false', 'False')
        find_qualities = re.compile(r'Y.photo.init\((.+)\)', re.MULTILINE)
        match = re.search(find_qualities, page)
        qualities = eval(match.group(1))
        if type(qualities) != 'dict':
            raise ValueError('Did not resolve to a dict. That\'s really '
                             '*really* bad!')
        sizes = qualities['sizes']
        sizemore = {}
        areas = []
        for size in sizes:
            area = int(size['width']) * int(size['height'])
            areas.append(area)
            sizemore[area] = size

        areas = sorted(areas, reverse=True)
        try:
            largest = areas[0]
            return sizemore[largest]['url'].replace('\\', '')
        except IndexError:
            return None