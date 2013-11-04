#Handles getting a single imgur image that isn't a direct link but rather a
# link to its imgur page

#works as of 02-23-13

import requests
from lxml import etree
from base_plugin import BasePlugin


class Get500pxSingle(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param dict candidate: data from a reddit post json
        """
        if candidate['data']['url'].lower().startswith('http://500px'
                                                       '.com/photo/'):
            img = self.get_500px_img(candidate['data']['url'])
            self.to_acquire.append({'url': img,
                                    'subreddit': candidate['data'][
                                    'subreddit'],
                                    'title': candidate['data']['title']})
            self.handled.append(candidate)

    def get_500px_img(self, url):
        """Helper for the 500px execute function

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """
        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error contacting imgur (%s):' % url
            print e
            return []
        tree = etree.HTML(resp.read())
        a = tree.findall('.//*[@id="thephoto"]/a')
        href = a[0].attrib['href']
        return href