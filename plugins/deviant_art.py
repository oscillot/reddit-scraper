#Handles getting the image url from the download button of a single image on
# deviant art

#works as of 02-23-13

import urllib
import urllib2
from lxml import etree
from base_plugin import BasePlugin


class DeviantArt(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param dict candidate: data from a reddit post json
        """
        if 'deviantart.com' in candidate['data']['url'].lower():
            deviant_art_img = self.get_deviant_art_image(candidate['data'][
                'url'])
            if deviant_art_img is not None:
                self.to_acquire.append({'url': deviant_art_img,
                                        'subreddit': candidate['data'][
                                            'subreddit'],
                                        'title': candidate['data']['title']})
                self.handled.append(candidate)

    def get_deviant_art_image(self, url):
        """Helper for the deviant art execute function

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """

        try:
            resp = urllib.urlopen(url)
        except urllib2.HTTPError, e:
            print 'Error reaching deviantart (%s):' % url
            print e
            return
        tree = etree.HTML(resp.read())
        for dl in tree.findall('.//*[@id="download-button"]'):
            if '/download/' in dl.attrib['href']:
                return dl.attrib['href']
        dl = tree.find('.//*/meta[@name="og:image"]')
        if dl is not None:
            return dl.attrib['content']