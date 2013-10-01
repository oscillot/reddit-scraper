import traceback


class BasePlugin():
    def __init__(self, candidates):
        """Constructs the plugin calls and executes them, saving successes,
        failures and links as class attributes

        :param list candidates: a list of dictionaries converted from the json
        response given back by reddit.
        :rtype list, list: a list of the dictionary data that was successfully
        parsed by this plugin, a list of dictionaries with the url,
        subreddit and title of the direct link for later acquisition and database
         entry
        """
        self.candidates = candidates
        self.to_acquire = []
        self.handled = []
        self.exceptions = []
        self.unavailable = []
        self.__execute()

    def __execute(self):
        """
        This hidden executor handles iterating through the list of links and
        catching any unexpected exceptions thrown by the plugin gracefully,
        reporting the plugin, link and exception for output at the end of the
         run
        """
        for candidate in self.candidates:
            try:
                self.execute(candidate)
            except Exception, e:
                #Trying this out for a bit
                e = traceback.format_exc()
                self.exceptions.append((candidate, e, self.__class__.__name__))

    def execute(self, candidate):
        """
        To be overridden by subclasses. The subclassed versions of this
        method should be written to handle just one post link,
        but can call other functions as needed.
        """
        pass