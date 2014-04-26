import unittest
from reddit_scraper.plugins.wallbase import Wallbase


class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches(self):
        url = 'http://wallbase.cc/wallpaper/1356861'
        self.assertTrue(Wallbase.url_matches(url))
        self.assertFalse(Wallbase.is_coll(url))
        self.assertTrue(Wallbase.is_wall(url))

    def test_url_not_matches(self):
        url = 'http://wallpapers.wallbase.cc/rozne/wallpaper-1356861.jpg'
        self.assertFalse(Wallbase.url_matches(url))

    def tearDown(self):
        pass
