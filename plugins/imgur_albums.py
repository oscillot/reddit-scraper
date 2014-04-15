#Handles getting all of the images from an album linked to on imgur
import re
from bs4 import BeautifulSoup
from plugins.base_plugin import *


class ImgurAlbum(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches():
            album_imgs = self.get_imgur_album(self.candidate.url)
            for album_img in album_imgs:
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        album_img)

    @staticmethod
    def url_matches(self):
        """
        This matches only imgur albums
        """

        imgur_alb_pat = re.compile(r'^http[s]?://.*imgur\.com/a/.*$',
                                   flags=re.IGNORECASE)
        if imgur_alb_pat.match(self.candidate.url):
            return True
        else:
            return False

    def get_imgur_album(self, url):
        """Helper for the imgur album execute function

        :param str url: a url to retrieve and execute the xpath on
        :rtype list: a list of urls that is are direct links to images
        """
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % url
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