import unittest

from reddit_scraper.util import extract_domain, substract


class TestExtractDomain(unittest.TestCase):
    def setUp(self):
        pass

    def test_extract_www_domain(self):
        url = 'http://www.deviantart.com'
        extracted = extract_domain(url)
        self.assertEqual(extracted, 'deviantart.com')

    def test_extract_just_domain(self):
        url = 'http://deviantart.com'
        extracted = extract_domain(url)
        self.assertEqual(extracted, 'deviantart.com')

    def test_extract_one_subdomain(self):
        url = 'http://oscillot.deviantart.com'
        extracted = extract_domain(url)
        self.assertEqual(extracted, 'deviantart.com')

    def test_extract_two_subdomains(self):
        url = 'http://oscillot.andfriends.deviantart.com'
        extracted = extract_domain(url)
        self.assertEqual(extracted, 'deviantart.com')

    def test_extract_three_subdomains(self):
        url = 'http://oscillot.and.friends.deviantart.com'
        extracted = extract_domain(url)
        self.assertEqual(extracted, 'deviantart.com')

    def test_extract_three_subdomains_with_tail(self):
        url = 'http://oscillot.and.friends.deviantart' \
              '.com/somefolder/hashsofsomesort/otherstuff/1234567890' \
              '/~userfolder/timedate01-23-04/unixtime/13019348623/image' \
              '.png?token=3418327129&other_param="some_other_stuff_to_ignore'
        extracted = extract_domain(url)
        self.assertEqual(extracted, 'deviantart.com')

    def test_substract_returns_sub(self):
        url = '/r/spaceclop/'
        self.assertEqual('spaceclop', substract(url))

    def test_substract_returns_original(self):
        url = '/r/spaceclop'
        self.assertEqual('/r/spaceclop', substract(url))