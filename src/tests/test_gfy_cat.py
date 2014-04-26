import unittest
from reddit_scraper.plugins.gfycat import GfyCat


class TestMatcher(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches(self):
        url = 'http://gfycat.com/SilentFirmDuckling'
        self.assertTrue(GfyCat.url_matches(url))

    def tearDown(self):
        pass