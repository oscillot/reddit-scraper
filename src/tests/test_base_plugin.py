import unittest
import requests
from reddit_scraper.plugins.base_plugin import BasePlugin
from reddit_scraper.config import get_config


class TestBasePlugin(unittest.TestCase):
    def setUp(self):
        self.base_plugin = BasePlugin(None, [], None, None, get_config(),
                                      False, True)
        self.base_plugin.resp = requests.Response()

    def test_basic_matcher(self):
        matcher = BasePlugin.get_basic_matcher('tangerinepulsar.com')
        self.assertTrue(matcher.match("http://tangerinepulsar.com"))

    def test_image_header_jpeg(self):
        self.base_plugin.resp.headers = {'content-type': "image/jpeg"}
        self.assertTrue(self.base_plugin.valid_image_header())

    def test_image_header_jpg(self):
        self.base_plugin.resp.headers = {'content-type': "image/jpg"}
        self.assertTrue(self.base_plugin.valid_image_header())

    def test_image_header_gif(self):
        self.base_plugin.resp.headers = {'content-type': "image/gif"}
        self.assertTrue(self.base_plugin.valid_image_header())

    def test_image_header_bmp(self):
        self.base_plugin.resp.headers = {'content-type': "image/bmp"}
        self.assertTrue(self.base_plugin.valid_image_header())

    def test_image_header_png(self):
        self.base_plugin.resp.headers = {'content-type': "image/png"}
        self.assertTrue(self.base_plugin.valid_image_header())

    def tearDown(self):
        pass