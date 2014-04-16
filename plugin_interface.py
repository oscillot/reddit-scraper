import os
import re

from data_types import DownloadList, CandidatesList
from plugins import loaded_plugins


def extract_domain(url):
    dom_pat = re.compile(r'^.*://(?:[wW]{3}\.)?([^:/]*).*$')
    domain = re.findall(dom_pat, url)[0]
    #truncate username subdomains like for e.g. deviant art and useless ones
    # like www
    if domain.count('.') > 1:
        #but don't be overzealous and do this on sites that end in like .co.uk
        if len(domain.split('.')[-2]) > 2:
            domain = '.'.join(domain.split('.')[-2:])
        else:
            if domain.count('.') > 2 and len(domain.split('.')[-2]) > 2:
                #alternate ruleset for e.g. .co.uk
                domain = '.'.join(domain.split('.')[1:])
    return domain


class PluginInterface():
    def __init__(self, database, candidates, output, categorize=False):
        """
        The PluginInterface takes care of reading the plugins, determining
        which ones are valid, and iterating through them. It is a wrapper
        around the plugins that makes sure that they are valid subclasses of
        the BasePlugin class.

        :param str database: the prefix for the database filename.
        :param list candidates: a list of candidate json objects from the
        `class` RedditConnect class
        :param str output: the location on disk to store your images (note
        that this can be changed and the database data will handle all
        duplicate filtering
        """
        self.database = database
        self.candidates = candidates
        self.output = output
        self.categorize = categorize
        #set up some class variables
        self.handled = DownloadList([])
        self.unhandled = DownloadList([])
        self.posts_already_finished = None
        self.image_urls_already_fetched = None
        self.candidates_backup = CandidatesList([])

    def hand_off_to_plugins(self):
        """Calls each plugin module and hand the CandidateList off to it.
        """
        for plugin in loaded_plugins:
            print 'Loading plugin: %s.\n' % plugin.__name__
            plug_inst = plugin(self.database, self.candidates, self.output,
                               self.categorize)
            for dl in plug_inst.handled:
                self.handled.add(dl)
            print '%s handled the following urls:\n' % plugin.__name__
            if len(plug_inst.handled) > 0:
                for h in plug_inst.handled:
                    print '\t', h.url
                print '\n'
            else:
                print '\tNone\n'
            #trim down the candidates from what got parsed
            self.candidates = plug_inst.revised
            self.handled.update(plug_inst.handled)
            self.candidates_backup.update(plug_inst.candidates_backup)
            #these two shouldn't(?) change so assigning them each time is fine
            self.posts_already_finished = plug_inst.posts_already_finished
            self.image_urls_already_fetched = \
                plug_inst.image_urls_already_fetched

    def check_unhandled_links(self):
        """
        Create a list of unhandled links along with domains for those
        links which we output at the end to help target plugin
        development/maintenance
        """
        all_handled = self.handled.union(
            self.image_urls_already_fetched).union(
                self.posts_already_finished)
        unhandled = self.candidates_backup.difference(all_handled)

        for each in unhandled:
            self.unhandled.add((extract_domain(each.url), each.url))

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

        #parse through links once and try to remove any unneeded plugins
        # (saves time once you have a lot of plugins)
        self.remove_unneeded_plugins()

        #parse links through plugins
        print '\nProcessing: parse links through plugins...'
        self.hand_off_to_plugins()

        print 'The following posts had links that were unhandled:'
        self.check_unhandled_links()
        if len(self.unhandled) > 0:
            #iterating through these sorted puts them in alpha order by domain
            #so you should be able to see which domains you want or need to
            # target
            for uh in sorted(self.unhandled):
                print uh[0], '\t', uh[1]
            print '\n'
        else:
            print 'None\n'

        print '\nComplete. %d new images were acquired this run.' \
              % len(self.handled)

    def remove_unneeded_plugins(self):
        plugins_count = {}
        for plugin in loaded_plugins:
            plugins_count[plugin] = 0
            for candidate in self.candidates:
                if plugin.url_matches(candidate['data']['url']):
                    plugins_count[plugin] += 1

        for plugin in plugins_count.keys():
            if plugins_count[plugin] == 0:
                print 'No matches for %s, unloading.' % plugin.__name__
                loaded_plugins.remove(plugin)