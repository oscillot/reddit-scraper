#Handles getting all of the images from an album linked to on imgur
import json
import re

from bs4 import BeautifulSoup

from reddit_scraper.plugins.base_plugin import *


def fixed_href(url):
    #Fix The single indirect links that look like this:
    #<link rel="image_src" href="//i.imgur.com/IZZayKa.png" />
    if not url.startswith('http://'):
        if url.startswith('//'):
            url = 'http:' + url
    return  url

class Imgur(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            if self.album_url(self.candidate.url):
                album_imgs = self.get_imgur_album(self.candidate.url)
                for album_img in album_imgs:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            album_img,
                                            self.candidate.nsfw)
            elif self.api_url(self.candidate.url):
                img_url = self.get_url_from_api()
                if img_url is not None:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            img_url,
                                            self.candidate.nsfw)
            #if you add more, try to keep this guy down at the bottom...
            # he tends to grab everything!
            elif self.image_url(self.candidate.url):
                img_url = self.get_imgur_single(self.candidate.url)
                if img_url is not None:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            img_url,
                                            self.candidate.nsfw)

    @staticmethod
    def url_matches(url):
        """
        This matches all of imgur
        """

        imgur_alb_pat = re.compile(r'^http[s]?://.*imgur\.com.*$',
                                   flags=re.IGNORECASE)
        if imgur_alb_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def album_url(url):
        """
        This matches only imgur albums
        """

        imgur_alb_pat = re.compile(r'^http[s]?://.*imgur\.com/a/.*$',
                                   flags=re.IGNORECASE)
        if imgur_alb_pat.match(url):
            return True
        else:
            return False

    @staticmethod
    def get_imgur_album(url):
        """Helper for the imgur album execute function

        :rtype list: a list of urls that is are direct links to images
        """
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % url
            print e
            return []
        soup = BeautifulSoup(resp.text)

        urls = []
        images = soup.find_all('div', attrs={'class': 'wrapper'})
        for image in images:
            found_url = image.find('a').attrs['href']
            urls.append(fixed_href(found_url))

        if not urls:
            #try to get an early warning next time this plugin stops working
            # for albums
            try:
                raise ValueError('No images found from album: %s' % url)
            except ValueError:
                pass

        return urls

#http://api.imgur.com/oembed.json?url=http://imgur.com/gallery/QLBhjdq

    @staticmethod
    def api_url(url):
        """
        This matches single imgur api calls that return JSON
        """

        imgur_single_page_pat = re.compile(
            r'^http[s]?://api\.imgur\.com/oembed\.json\?.*$',
            flags=re.IGNORECASE)
        #strip the url args since we are looking to match against file types
        if imgur_single_page_pat.match(url):
            return True
        else:
            return False

    def get_url_from_api(self):
        try:
            resp = requests.get(self.candidate.url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % self.candidate.url
            print e
            return []
        api_data = json.loads(resp.content)
        if 'url' in api_data.keys():
            return api_data['url']
        elif 'src' in api_data.keys():
            return api_data['src'].rstrip('/embed/')


#Handles getting a single imgur image that isn't a direct link but rather a
# link to its imgur page
    @staticmethod
    def image_url(url):
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

    @staticmethod
    def get_imgur_single(url):
        """Helper for the imgur single image page function

        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % url
            print e
            return []
        root = BeautifulSoup(resp.content)
        al = root.find_all(attrs={'class': 'image textbox '})
        for a in al:
            href = a.img.attrs.get('src')

            return fixed_href(href)
