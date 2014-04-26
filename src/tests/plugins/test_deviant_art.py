import unittest
from reddit_scraper.plugins.deviant_art import DeviantArt


class TestMatcher(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches_no_ext(self):
        url = 'http://nimrohil.deviantart.com/art/Scifi-scene-363369030'
        self.assertTrue(DeviantArt.url_matches(url))

    def test_url_not_matches_with_ext(self):
        url = 'http://nimrohil.deviantart.com/art/Scifi-scene-363369030.png'
        self.assertFalse(DeviantArt.url_matches(url))
