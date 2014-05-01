from reddit_scraper.singleton import Singleton


class PluginNeedsUpdated(Exception):
    def __init__(self, message):
        self.message = message
        super(PluginNeedsUpdated, self).__init__(message)

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value
        c = PluginExceptionCounter.Instance()
        c.increment()


@Singleton
class PluginExceptionCounter(object):
    def __init__(self):
        self._counter = 0

    def increment(self):
        self._counter += 1

    def get_count(self):
        return self._counter