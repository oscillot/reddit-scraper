import unittest
from reddit_scraper.singleton import Singleton


@Singleton
class MockClass(object):
    def __init__(self):
        pass


class TestSingleton(unittest.TestCase):
    def setUp(self):
        self.klass1 = MockClass.Instance()
        self.klass2 = MockClass.Instance()

    def test_singleton_id(self):
        self.assertEqual(id(self.klass1), id(self.klass2))