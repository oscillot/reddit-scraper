import unittest
from reddit_scraper.plugins.imgur import Imgur


class TestMatcher(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches_album_no_subdomain(self):
        url = 'http://imgur.com/a/7qFIc'
        self.assertTrue(Imgur.url_matches(url))

    def test_url_matches_album_no_subdomain2(self):
        url = 'http://imgur.com/a/kfkmK'
        self.assertTrue(Imgur.url_matches(url))

    def test_url_matches_single_indirect(self):
        url = 'http://imgur.com/wtD08iT'
        self.assertTrue(Imgur.url_matches(url))

    def test_url_not_matches_single_direct(self):
        url = 'http://imgur.com/wtD08iT.jpg'
        self.assertFalse(Imgur.url_matches(url))

    def tearDown(self):
        pass