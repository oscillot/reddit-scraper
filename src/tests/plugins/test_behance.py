import unittest
from reddit_scraper.plugins.behance_gallery import BehanceGallery


class TestBehance(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches(self):
        url = 'http://www.behance.net/gallery/portfolio-2/1763950'
        self.assertTrue(BehanceGallery.url_matches(url))

    def test_url_not_matches(self):
        url = 'http://m1.behance.net/rendition/modules/12621812/hd/a8ba669c129c9880e5a39386b5d7bf10.jpg'
        self.assertFalse(BehanceGallery.url_matches(url))

    def tearDown(self):
        pass
