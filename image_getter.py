import os
import re

from plugins import loaded_plugins


def extract_domain(url):
    dom_pat = re.compile(r'^.*://(?:[wW]{3}\.)?([^:/]*).*$')
    domain = re.findall(dom_pat, url)[0]
    if domain.count('.') > 1:
        domain = '.'.join(domain.split('.')[-2:])
    return domain


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

    def hand_off_to_plugins(self):
        """Call each plugin module and hand the list of unhandled links off to
        it. Plugin *must* return a list of the links that were successfully
        handled AND a list of to_acquire where each member of that list is
        a dictionary with the following keys: 'url', 'subreddit', 'title'

        """
        self.candidates_backup = set()
        for plugin in loaded_plugins:
            print 'Loading plugin: %s.' % plugin.__name__
            plug_inst = plugin(self.database, self.candidates, self.output)
            self.handled.extend(plug_inst.handled)
            print '%s handled the following links:' % \
                  plugin.__name__
            if len(plug_inst.handled) > 0:
                for h in plug_inst.handled:
                    print h.url
                print '\n'
            else:
                print 'None\n'
            #trim down the candidates from what got parsed
            self.candidates = plug_inst.revised
            #the last instance of these should be fine
            self.posts_already_finished = plug_inst.posts_already_finished
            self.image_urls_already_fetched = plug_inst.image_urls_already_fetched
            self.candidates_backup.update(plug_inst.candidates_backup)

    def check_unhandled_links(self):
        for original in self.candidates_backup:
            if original in self.handled or original in \
                    self.image_urls_already_fetched or \
                    original in self.posts_already_finished:
                continue
            else:
                self.unhandled.append((extract_domain(original.url),
                                       original.url))

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
        self.check_unhandled_links()
        if len(self.unhandled) > 0:
            for uh in sorted(self.unhandled):
                print uh[0], '\t', uh[1]
            print '\n'
        else:
            print 'None\n'

        print '\nComplete. %d new images were acquired this run.' \
              % len(self.handled)