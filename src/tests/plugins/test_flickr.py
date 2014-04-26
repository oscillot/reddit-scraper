import unittest
from reddit_scraper.plugins.flickr import Flickr


class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_url_matches(self):
        url = 'http://www.flickr.com/photos/nonconmat/8664511804/in/photostream/lightbox/'
        self.assertTrue(Flickr.url_matches(url))

    def test_url_not_matches(self):
        url = 'http://farm6.staticflickr.com/5086/5353184142_9f318e3817_o.jpg'
        self.assertFalse(Flickr.url_matches(url))

    def tearDown(self):
        pass