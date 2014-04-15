import re
from plugins.base_plugin import *


class DirectLinks(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if self.url_matches():
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
                                            self.candidate.url)
                    break

    @staticmethod
    def url_matches(self):
        """
        This is just a link that looks like it's a direct link to an image
        """
        direct_pat = re.compile(r'^http[s]?://.*(?:.jpg|.jpeg|.gif|.bmp|.png).*$',
                                flags=re.IGNORECASE)
        if direct_pat.match(self.candidate.url):
            return True
        else:
            return False