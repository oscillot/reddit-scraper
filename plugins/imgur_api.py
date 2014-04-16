#http://api.imgur.com/oembed.json?url=http://imgur.com/gallery/QLBhjdq

import re
import json
from plugins.base_plugin import *


class ImgurAPI(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        #prevent this plugin from handling links such as the following:
        #http://i.imgur.com/nbsQ4SF.jpg#.UTtRkqYGmy0.reddit
        if self.url_matches(self.candidate.url):
            img_url = self.get_url_from_api()
            if img_url is not None:
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        img_url)

    @staticmethod
    def url_matches(url):
        """
        This matches single imgur api calls that return JSON
        """

        imgur_single_page_pat = re.compile(
            r'^http[s]?://api\.imgur\.com/oembed\.json.*$',
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
        return api_data['url']
