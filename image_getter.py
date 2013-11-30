import os

from plugins import *


class ImageGetter():
    def __init__(self, database, candidates, output):
        """The ImageGetter class handles all of the logic necessary to
        translate data from reddit (in this case, a filtered list of upvoted
        posts is input) and enumerates any that it can into listings of
        direct links. The goal at the end is to have every possible upvoted
        image link parsed into a direct link or links for retrieval. Then
        links can be retrieved and a slew of metadata is tokenized into a
        database that tracks which posts have already been acquired,
        which links have already been acquired, and at its most granular
        level, the md5 of every image already acquired. It tries to retrieve
        as little as possible using this progressive keyspace reduction,
        the worst case scenario being that it might retrieve the same image
        from two disparate sources, but then chuck it right at the end
        because of the MD5 check.

        :param str database: the prefix for the database filename.
        :param list candidates: a list of dictionaries converted from the json
        :param str output: the location on disk to store your images (note
        that this can be changed and the database data will handle all
        duplicate filtering
        """
        self.database = database
        self.candidates = candidates
        self.output = output
        self.handled = []
        self.unhandled = []
        self.exceptions = []

    def hand_off_to_plugins(self):
        """Call each plugin module and hand the list of unhandled links off to
        it. Plugin *must* return a list of the links that were successfully
        handled AND a list of to_acquire where each member of that list is
        a dictionary with the following keys: 'url', 'subreddit', 'title'

        """

        for plugin in loaded_plugins:
            print 'Loading plugin: %s.' % plugin.__name__
            plug_inst = plugin(self.database, self.candidates, self.output)
            handled = plug_inst.handled
            self.handled.extend(handled)
            self.exceptions.extend(plug_inst.exceptions)
            self.unhandled.extend(plug_inst.unavailable)
            print 'Plugin handled the following links:'
            if len(handled) > 0:
                for h in handled:
                    print h['data']['url']
                print '\n'
            else:
                print 'None\n'


    def acquire(self):
        """
        Handles the calls to the database and the requests out to the world
        for the image candidates. This handles images returned directly as
        well as gzipped images and does all of the reads and writes to and
        from the database. Images that are already in the database are
        skipped. This is done on a filename only basis and is not very smart if
         say there are two different images called "image1.jpg" for example.

        :param list candidates: The list of dictionaries that is returned
        from :func: get_upvoted_wallpapers, where each 'url' key s a direct
        link to an image.
        :param str output: The location to save the downloaded images to as a
         string
        """
        if not os.path.exists(self.output):
            os.makedirs(self.output)

        #parse links through plugins
        print '\nProcessing: parse links through plugins...'
        self.hand_off_to_plugins()

        print 'The following posts had links that were unhandled:'
        if len(self.unhandled) > 0:
            for uh in self.unhandled:
                print uh['data']['url']
                print '\n'
        else:
            print 'None'

        print 'The following links caused plugin exceptions:'
        if len(self.exceptions) > 0:
            for link, ex, plugin in self.exceptions:
                print '%s: %s - %s' % (plugin, link['data']['url'], ex)
        else:
            print 'None'

        print '\nComplete. %d new images were acquired this run.' \
              % len(self.handled)