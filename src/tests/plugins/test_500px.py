import unittest
from reddit_scraper.plugins.px500 import PX500


class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches(self):
        url = 'http://500px.com/photo/13746291/shining-through-by-paul-rojas?utm_campaign=apr26_2PM_landscape_shiningthrough13746291&utm_medium=google&utm_source=500px'
        self.assertTrue(PX500.url_matches(url))
        self.assertTrue(PX500.is_image(url))

    def test_url_not_matches(self):
        url = 'http://ppcdn.500px.org/13746291/14f891acd54bacde18f130773e3880b60e9f3fa4/5.jpg'
        self.assertFalse(PX500.url_matches(url))

    def tearDown(self):
        pass