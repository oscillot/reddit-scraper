import unittest
from reddit_scraper.plugins.imgur import Imgur


class TestMatcher(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches_album_no_subdomain(self):
        url = 'http://imgur.com/a/7qFIc'
        self.assertTrue(Imgur.url_matches(url))
