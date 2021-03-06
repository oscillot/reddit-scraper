import re

from reddit_scraper.plugins.base_plugin import BasePlugin
from reddit_scraper.data_types import Download


class DirectLinks(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches(self.candidate.url):
            #This helps handle the new imgur links that are direct links but
            # have some kind of reddit argument e.g.
            # http://i.imgur.com/nbsQ4SF.jpg#.UTtRkqYGmy0.reddit
            if self.candidate.url.startswith('http://i.imgur.com') and \
                    self.candidate.url.endswith('.reddit'):
                self.candidate.url = self.candidate.url.split('#')[0]
            for img_type in ['.jpg', '.jpeg', '.gif', '.bmp', '.png']:
                if self.candidate.url.lower().rsplit('?')[0].endswith(
                        img_type):
                    self.current = Download(self.candidate.title,
                                            self.candidate.subreddit,
                                            self.candidate.url,
                                            self.candidate.nsfw)
                    break

    @staticmethod
    def url_matches(url):
        """
        This is just a link that looks like it's a direct link to an image
        """
        direct_pat = re.compile(r'^https?://.*' #any webpage
                                r'(' #that ends with
                                    r'(.jpg|' #jpg
                                    r'.jpeg|' #jpeg
                                    r'.gif|'  #gif
                                    r'.bmp|'  #bmp
                                    r'.png)'  #png
                                    r'([#?&0-9a-zA-Z\-_]*)' #optionally with anchors or parameters
                                r')$', #at end of string
                                flags=re.IGNORECASE)
        if direct_pat.match(url):
            return True
        else:
            return False