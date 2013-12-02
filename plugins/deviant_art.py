import requests
from lxml import etree
from plugins.base_plugin import *


class DeviantArt(BasePlugin):
    def execute(self):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        """
        if 'deviantart.com' in self.candidate.url.lower():
            deviant_art_img_url = self.get_deviant_art_image(self.candidate.url)
            if deviant_art_img_url is not None:
                if deviant_art_img_url == 'deviantART: 404 Not Found':
                    return
                self.current = Download(self.candidate.title,
                                        self.candidate.subreddit,
                                        deviant_art_img_url)

    def get_deviant_art_image(self, url):
        """Helper for the deviant art execute function

        :param str url: a url to retrieve and execute the xpath on
        :rtype str: a url that is a direct link to an image
        """

        try:
            resp = requests.get(url)
        except requests.HTTPError, e:
            print 'Error reaching deviantart (%s):' % url
            print e
            return
        tree = etree.HTML(resp.text)
        #/html/head/title
        for title in tree.findall('.//head/title'):
            if title.text == 'deviantART: 404 Not Found':
                print '%s: %s' % (url, title.text)
                return title.text
        #//*[@id="output"]/div[1]/div[4]/div[1]/div/div[2]/a
        for dl in tree.findall(".//*/a[@class='dev-page-button dev-page-button-with-text dev-page-download']"):
            if dl is not None and dl.get('href'):
                if '/download/' in dl.attrib['href']:
                    href = dl.attrib['href']
                    if '?token' in href:
                        href = href.split('?token')[0]
                    return href
        #Possibly the above catches all images as of 9-30, not sure yet
        for dl in tree.findall('.//*[@id="download-button"]'):
            if dl is not None and dl.get('href'):
                if '/download/' in dl.attrib['href']:
                    return dl.attrib['href']
        dl = tree.find('.//*/meta[@name="og:image"]')
        if dl is not None:
            return dl.attrib['content']


