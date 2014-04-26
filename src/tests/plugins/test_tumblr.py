import unittest
from reddit_scraper.plugins.tumblr import Tumblr


class TestMatcher(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches_no_ext(self):
        url = 'http://n6jlv.tumblr.com/post/83763121262/thanks-alan-you-are-an-amazing-photographer'
        self.assertTrue(Tumblr.url_matches(url))

    def test_url_not_matches_ext(self):
        url = 'https://31.media.tumblr.com/bbc3c46117883865c4db4799d969a94e/tumblr_n44sxfZ2V31t8n9z2o1_500.gif'
        self.assertFalse(Tumblr.url_matches(url))

    def tearDown(self):
        pass
