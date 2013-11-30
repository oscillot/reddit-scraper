from plugins.base_plugin import *


class DirectLinks(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param Download candidate: data from a reddit post json
        """
        #This helps handle the new imgur links that are direct links but have
        #  some kind of reddit argument e.g.
        # http://i.imgur.com/nbsQ4SF.jpg#.UTtRkqYGmy0.reddit
        if candidate.url.startswith('http://i.imgur.com') and \
                candidate.url.endswith('.reddit'):
            candidate.url = candidate.url.split('#')[0]
        for img_type in ['.jpg', '.jpeg', '.gif', '.bmp', '.png']:
            if candidate.url.lower().rsplit('?')[0].endswith(
                    img_type):
                self.current = Download(candidate.title,
                                        candidate.subreddit,
                                        candidate.url.rsplit('?')[0])
                break