#Handles getting a single imgur image that isn't a direct link but rather a
# link to its imgur page
import re
from bs4 import BeautifulSoup
from plugins.base_plugin import *


class ImgurSingleIndirect(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        #prevent this plugin from handling links such as the following:
        #http://i.imgur.com/nbsQ4SF.jpg#.UTtRkqYGmy0.reddit
        if self.url_matches(self.candidate.url):
            img_url = self.get_imgur_single()
            if img_url is not None:
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        img_url)

    @staticmethod
    def url_matches(url):
        """
        This matches single image pages on imgur that are not direct links to
        the image. Yeah, look at that sexy regex. Nested non-captureing groups
        with a negative lookahead assertion. What's that? Oh! Two negative
        look ahead assertions!

        That's so sexy!

        If you are reading this my wife is e-mailing me YouTube videos of Hulk
        Hogan cartoons and a Kid and Play music video, also with cartoons. Go
        and watch those!
        """

        imgur_single_page_pat = re.compile(
            r'^http[s]?://' #an imgur page
            r'(?!(?:.*imgur\.com/a/|' #that is not an album
            r'api\.imgur\.com/oembed\.json\?))' #and not from the imgur API
            r'.*imgur\.com' #from any subdomain
            r'(?:(?![.]{1}(?:' #that doesn't end with the extension
                r'jpg|' #jpeg
                r'jpeg|' #jpeg
                r'gif|' #gif
                r'bmp|' #bitmap
                r'png)' #png
            r').)*$',
            flags=re.IGNORECASE)
        #strip the url args since we are looking to match against file types
        if imgur_single_page_pat.match(url.split('#')[0]):
            return True
        else:
            return False

    def get_imgur_single(self):
        """Helper for the imgur single image page function

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(self.candidate.url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % self.candidate.url
            print e
            return []
        root = BeautifulSoup(resp.text)
        al = root.find('head').find_all('link')
        for a in al:
            href = a.attrs.get('href')
            if self.candidate.url.lstrip('http://') in href:
                #Fix The single indirect links that look like this:
                #<link rel="image_src" href="//i.imgur.com/IZZayKa.png" />
                if not href.startswith('http://'):
                    if href.startswith('//'):
                        href = 'http:' + href
                return href