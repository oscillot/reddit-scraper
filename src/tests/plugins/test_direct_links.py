import unittest
from reddit_scraper.plugins.direct_links import DirectLinks


class TestMatcher(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches(self):
        url = 'http://www.fromquarkstoquasars.com/wp-content/uploads/2014/08/he-Elephant\xE2\x80\x99s-Trunk-nebula-in-3D..gif'
        self.assertTrue(DirectLinks.url_matches(url))

    def tearDown(self):
        pass
