#Handles getting all of the images from an album linked to on imgur

#works as of 02-23-13

import requests
from lxml import etree
from base_plugin import BasePlugin


class ImgurAlbum(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param dict candidate: data from a reddit post json
        """
        if candidate['data']['url'].lower().startswith('http://imgur.com/a/'):
            album_imgs = self.get_imgur_album(candidate['data']['url'])
            for album_img in album_imgs:
                #This handles the links that come down with extensions like
                # `jpg?1` that have been showing up lately. Regular links
                # should be unaffected by this. This is done here so that the
                #  list of handled links is still accurate.
                self.to_acquire.append({'url': album_img.split('?')[0],
                                       'subreddit': candidate['data'][
                                           'subreddit'],
                                       'title': candidate['data']['title']})
            self.handled.append(candidate)

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
        tree = etree.HTML(resp.text)
        urls = []
        for script in tree.findall('body/script'):
            if script.text is not None:
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