import unittest
from reddit_scraper.exceptions import PluginNeedsUpdated, \
    PluginExceptionCounter


class TestExceptions(unittest.TestCase):
    def setUp(self):
        self.counter = PluginExceptionCounter.Instance()

    def test_raise_plugin_exc_incs_counter(self):
        for r in range(10):
            try:
                raise PluginNeedsUpdated('unittest')
            except PluginNeedsUpdated:
                pass

        self.assertEqual(self.counter.get_count(), 10)