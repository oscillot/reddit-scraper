#Handles getting all of the images from an album linked to on imgur
import json
import re

from bs4 import BeautifulSoup

from src.reddit_scraper.plugins.base_plugin import *


class Imgur(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            if self.album_url():
                album_imgs = self.get_imgur_album()
                for album_img in album_imgs:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            album_img,
                                            self.candidate.nsfw)
            elif self.api_url():
                img_url = self.get_url_from_api()
                if img_url is not None:
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            img_url,
                                            self.candidate.nsfw)
            #if you add more, try to keep this guy down at the bottom...
            # he tends to grab everything!
            elif self.image_url():
                img_url = self.get_imgur_single()
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

    def album_url(self):
        """
        This matches only imgur albums
        """

        imgur_alb_pat = re.compile(r'^http[s]?://.*imgur\.com/a/.*$',
                                   flags=re.IGNORECASE)
        if imgur_alb_pat.match(self.candidate.url):
            return True
        else:
            return False

    def get_imgur_album(self):
        """Helper for the imgur album execute function

        :rtype list: a list of urls that is are direct links to images
        """
        try:
            resp = requests.get(self.candidate.url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % self.candidate.url
            print e
            return []
        root = BeautifulSoup(resp.text)
        urls = []
        for script in root.find('body').find_all('script'):
            if script.attrs.get('text') is not None:
                if script.text.replace('\n', '').lstrip().rstrip()\
                        .startswith('var album'):
                    album = eval('[{%s}]' % script.text.split('[{')[1].split(
                        '}]')[0])
                    #this check in case the album has one image,
                    # which returns dict instead of list
                    if type(album) == list or type(album) == tuple:
                        for image in album:
                            url = 'http://i.imgur.com/%s%s' % (image['hash'],
                                                               image['ext'])
                            urls.append(url)
                    elif type(album) == dict:
                        url = 'http://i.imgur.com/%s%s' % (album['hash'],
                                                           album['ext'])
                        urls.append(url)
                    else:
                        print type(album), album
                        print 'Unhandled album type!'
                        raise ValueError
        return urls

#http://api.imgur.com/oembed.json?url=http://imgur.com/gallery/QLBhjdq

    def api_url(self):
        """
        This matches single imgur api calls that return JSON
        """

        imgur_single_page_pat = re.compile(
            r'^http[s]?://api\.imgur\.com/oembed\.json\?.*$',
            flags=re.IGNORECASE)
        #strip the url args since we are looking to match against file types
        if imgur_single_page_pat.match(self.candidate.url):
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

    def image_url(self):
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
        if imgur_single_page_pat.match(self.candidate.url.split('#')[0]):
            return True
        else:
            return False

    def get_imgur_single(self):
        """Helper for the imgur single image page function

        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(self.candidate.url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % self.candidate.url
            print e
            return []
        root = BeautifulSoup(resp.text)
        al = root.find_all(attrs={'class': 'image textbox '})
        for a in al:
            href = a.img.attrs.get('src')
            #Fix The single indirect links that look like this:
            #<link rel="image_src" href="//i.imgur.com/IZZayKa.png" />
            if not href.startswith('http://'):
                if href.startswith('//'):
                    href = 'http:' + href
            return href