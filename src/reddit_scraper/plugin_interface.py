import os
import re
import unicodedata

from reddit_scraper.data_types import CandidatesList
from reddit_scraper.plugins import loaded_plugins


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
    def __init__(self, database, candidates, output, categorize=False,
                 nsfw=False):
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
        self.nsfw = nsfw
        if self.nsfw:
            nsfw_flag = 'enabled'
        else:
            nsfw_flag = 'disabled'
        print '\nFetching NSFW Images is %s.\n' % nsfw_flag
        #set up some class variables
        self.handled_posts = {}
        self.unhandled_posts = set()
        self.posts_already_finished = None
        self.image_urls_already_fetched = None
        self.candidates_backup = CandidatesList(set())

    def hand_off_to_plugins(self):
        """Calls each plugin module and hand the CandidateList off to it.
        """
        for plugin in loaded_plugins:
            print 'Loading plugin: %s.\n' % plugin.__name__
            plug_inst = plugin(self.database, self.candidates, self.output,
                               self.categorize, self.nsfw)
            self.handled_posts.update(plug_inst.handled_posts)

            #lazy instantiation so we only get it on the first loop
            if len(self.candidates_backup) == 0:
                # candidates backup is the original list of candidates
                self.candidates_backup.update(plug_inst.candidates_backup)

            #trim down the candidates from what got parsed
            self.candidates = plug_inst.revised

            #these two shouldn't(?) change so assigning them each time is fine
            self.posts_already_finished = plug_inst.posts_already_finished
            self.image_urls_already_fetched = \
                plug_inst.image_urls_already_fetched

            print '%s handled the following posts:\n' % plugin.__name__
            if len(plug_inst.handled_posts):
                for post in plug_inst.handled_posts:
                    # print post.title.encode('ascii', 'xmlcharrefreplace')
                    print '%s (%s)' % \
                          (unicodedata.normalize(post.title, 'NFD').encode(
                              'ascii', 'xmlcharrefreplace'), post.url)

                    print '\n\t...which provided the following image urls:\n'
                    for link in plug_inst.handled_posts[post]:
                        print '\t%s\n' % link.url
            else:
                print 'None.'
            print '\n'

    def check_unhandled_posts(self):
        """
        Create a list of unhandled posts along with domains for those
        links which we output at the end to help target plugin
        development/maintenance
        """
        handled_posts = self.handled_posts.keys()

        # self.image_urls_already_fetched
        # self.posts_already_finished

        unhandled_posts = self.candidates_backup.difference(handled_posts)

        for each in unhandled_posts:
            self.unhandled_posts.add(
                (extract_domain(each.url), '%s (%s)' %
                    (unicodedata.normalize(each.title, 'NFD').encode(
                        'ascii', 'xmlcharrefreplace'), each.url)))

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
        self.check_unhandled_posts()
        if len(self.unhandled_posts) > 0:
            #iterating through these sorted puts them in alpha order by domain
            #so you should be able to see which domains you want or need to
            # target
            for uh in sorted(self.unhandled_posts):
                print uh[0], '\t', uh[1]
            print '\n'
        else:
            print 'None\n'

        print '\nComplete. %d new images were acquired this run.' \
              % sum([len(self.handled_posts[p]) for p in self.handled_posts])

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