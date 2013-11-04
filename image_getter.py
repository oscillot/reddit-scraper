import sys
import os
import gzip
import urllib
import urllib2
from StringIO import StringIO
import hashlib
from sqlalchemy import *
import sqlalchemy.sql as sql
from PIL import Image
from base_plugin import BasePlugin

IMAGE_HEADERS = ['image/bmp',
                 'image/png',
                 'image/jpg',
                 'image/jpeg',
                 'image/gif']

#Platform agnostic handler for paths
#*NOTE* This assumes that on *nix systems you will install this to the root
# of your user folder
if 'linux' in sys.platform.lower():
    APP_ROOT = os.path.expanduser('~')
elif sys.platform.startswith('win'):
    APP_ROOT = 'C:\\'

#Load an arbitrary number of arbitrarily named plugins from the plugins folder
plugins_folder = os.path.join(APP_ROOT, 'reddit-scraper', 'plugins')
plugin_list = []
for r, d, f in os.walk(plugins_folder):
    for p in f:
        if p.endswith('.py'):
            plugin_list.append(p.rstrip('.py'))

sys.path.insert(0, plugins_folder)
loaded_plugins = []
failed_plugins = []
succeeded = []
for plugin in plugin_list:
    try:
        loaded = __import__(plugin)
        for attr in dir(loaded):
            try:
                cls = getattr(loaded, attr)
                if issubclass(cls, BasePlugin) and cls.__name__ != 'BasePlugin':
                    loaded_plugins.append(cls)
                    succeeded.append(cls.__name__)
            except TypeError:
                pass
    except ImportError, e:
        print '%s:%s failed to load: %s\n' % (plugin, cls, e)
        failed_plugins.append(cls.__name__)
sys.path.remove(plugins_folder)
print 'Loaded the following plugins successfully: %s\n' % ', '.join(succeeded)


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

        self.output = output
        self.to_acquire = []
        self.handled = []
        self.db = os.path.join(os.getcwd(), '%s_downloaded.db' % database)
        self.engine = create_engine('sqlite:///%s' % self.db)
        metadata = MetaData(self.engine)
        self.wallpapers = Table('wallpapers', metadata,
                                Column('subreddit', String),
                                Column('title', String),
                                Column('url', String),
                                Column('filename', String),
                                Column('md5', String, primary_key=True)
        )
        self.retrieved = Table('retrieved', metadata,
                               Column('image_url', String,
                                      primary_key=True))
        self.errors = Table('errors', metadata,
                            Column('image_url', String,
                                   primary_key=True),
                            Column('attempts', Integer))
        #Create the DB tables if not there
        metadata.create_all()
        self.list_previous_handled_posts()
        self.candidates = candidates
        for cand in candidates:
            if cand['data']['url'] not in self.already_handled:
                self.already_handled.append(cand['data']['url'])
            else:
                self.candidates.remove(cand)
                print 'Skipping previously acquired post: %s' % cand['data'][
                    'url']
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
            plug_inst = plugin(self.candidates)
            handled = plug_inst.handled
            self.handled.extend(handled)
            self.to_acquire.extend(plug_inst.to_acquire)
            self.exceptions.extend(plug_inst.exceptions)
            self.unhandled.extend(plug_inst.unavailable)
            print 'Plugin handled the following links:'
            if len(handled) > 0:
                for h in handled:
                    print h['data']['url']
                print '\n'
            else:
                print 'None\n'
            #remove handled links here so each plugin doesn't have to do this
            # itself
            for h in handled:
                self.candidates.remove(h)
                if h in self.unhandled:
                    self.unhandled.remove(h)
            if len(self.candidates) > 0:
                for c in self.candidates:
                    #inform of any unhandled cases
                    if c not in self.unhandled:
                        self.unhandled.append(c)

    def check_redirects(self):
        """
        A simple but effective check to see if an image link points to a
        redirect. This is ot executed until after the first pass at retrieval
        . Only remaining unhandled links are evaluated and if there are no
        remaining unhandled links, the second pass is never performed.
        """
        redirects_found = False
        for link in self.unhandled:
            print 'Checking: %s' % link['data']['url']
            resp = urllib.urlopen(link['data']['url'])
            redirected = resp.geturl()
            if redirected != link['data']['url']:
                redirects_found = True
                print '%s redirects to: %s' % (link['data']['url'], redirected)
                if link in self.candidates:
                    self.candidates.remove(link)
                if link in self.unhandled:
                    self.unhandled.remove(link)
                link['data']['url'] = redirected
                self.candidates.append(link)
        return redirects_found

    def handle_exception(self, error, candidate):
        """
        To be called when an exception is caught or raised that prevents the
        image from being acquired. Error is put into the database for use
        later. After 5 errors the link is no longer tried.
        """
        print '%s\n' % str(error)
        self.unhandled.append({'data': candidate}) #this is a compatibility
        # hack bc i did something stupid somewhere
        url = candidate['url']
        err_urls = sql.select([self.errors])
        conn = self.engine.connect()
        errs = [e['image_url'] for e in conn.execute(err_urls).fetchall()]
        if url not in errs:
            err_ins = self.errors.insert((url, 1))
            conn.execute(err_ins)
        else:
            old_att_sel = sql.select([self.errors]).where(self.errors.c
                                                          .image_url == url)
            old_attempts = conn.execute(old_att_sel).fetchone()[1]
            err_upd = self.errors.update().where(self.errors.c.image_url ==
                                                 url).values({'attempts':
                                                              old_attempts +
                                                              1})
            conn.execute(err_upd)

    def too_many_error_attempts(self, candidate):
        """
        This checks the database for the number of times a link has errored
        and returns True or False for is it has errored 5 or more times.
        """
        conn = self.engine.connect()
        url = candidate['url']
        err_urls = sql.select([self.errors])
        errs = [e['image_url'] for e in conn.execute(err_urls).fetchall()]
        if url not in errs:
            return False
        att_sel = sql.select([self.errors]).where(self.errors.c
                                                  .image_url == url)
        attempts = conn.execute(att_sel).fetchone()[1]
        if attempts < 5:
            return False
        else:
            return True

    def get_previous_md5s(self):
        """
        Returns the list of md5s already in the database
        """
        conn = self.engine.connect()
        md5_select = sql.select(from_obj=self.wallpapers, columns=['md5'])
        unique_img_hashes = [h[0] for h in conn.execute(md5_select).fetchall()]
        return unique_img_hashes

    def list_previous_handled_posts(self):
        """
        Returns the list of previous liked posts that successfully went all
        the way through the scraper
        """
        conn = self.engine.connect()
        retrieved_select = sql.select([self.retrieved])
        self.already_handled = [a[0] for a in conn.execute(retrieved_select)
        .fetchall()]

    def list_handled_image_links(self):
        """
        Returns the ist of urls that has successfully been handled.
        """
        conn = self.engine.connect()
        handled_select = sql.select([self.wallpapers])
        self.already_dled = [a[2] for a in conn.execute(handled_select)
        .fetchall()]

    def add_to_previous_aquisitions(self):
        """
        Adds to the list of previously handled links
        """
        #prevent hash collision in the table
        uniques = set()
        for h in self.handled:
            if h['data']['url'] not in self.already_handled:
                uniques.add(h['data']['url'])
        for u in uniques:
            conn = self.engine.connect()
            retrieved_ins = sql.insert(table=self.retrieved,
                                       values=[u])
            conn.execute(retrieved_ins)

    def add_to_main_db_table(self, candidate, md5):
        """
        Inserts the full handled link info into the wallpaers table of the db
        """
        conn = self.engine.connect()
        wall_data = (candidate['subreddit'], candidate['title'],
                     candidate['url'], candidate['filename'], md5)
        wall_ins = self.wallpapers.insert(wall_data)
        conn.execute(wall_ins)

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

        #first pass: parse links through plugins
        print '\nFirst pass...'
        self.hand_off_to_plugins()
        #check remainder for redirects
        print "Checking remainder for redirects or shortened urls"
        if self.check_redirects():
            #hand the modified list off a 2nd time to try to get any stragglers
            print '\nSecond pass for redirects...'
            self.hand_off_to_plugins()
        else:
            print 'No redirects detected.\n'
        print 'Candidates retrieved!\n'
        new = 0
        print 'Found %d candidates.\n' % len(self.to_acquire)
        print 'Getting wallpapers...\n'
        unique_img_hashes = self.get_previous_md5s()
        total = len(self.to_acquire)
        for i, candidate in enumerate(self.to_acquire):
            candidate['filename'] = candidate['url'].split('/')[-1].replace(
                ' ', '_')
            self.list_handled_image_links()
            if candidate['url'] in self.already_dled:
                print 'Skipping #%d/%d: %s has already been downloaded\n' % (
                    i + 1, total, candidate['filename'])
                continue
            if self.too_many_error_attempts(candidate):
                print 'Skipping #%d/%d: %s has failed 5 or more times\n' % (
                    i + 1, total, candidate['filename'])
                continue
            print 'Aquiring #%d/%d: %s \n' % (i, total, candidate['filename'])
            for key in ['subreddit', 'url', 'title']:
                print candidate[key].encode('ascii', 'replace')
            print '\n'
            try:
                resp = urllib.urlopen(candidate['url'])
            except urllib2.HTTPError, e:
                self.handle_exception(e, candidate)
                continue

            if resp.headers.get('content-type') not in IMAGE_HEADERS:
                e = ValueError('Non-image header \"%s\" was found at the '
                               'link: %s' % (resp.headers.get('content-type'),
                                             candidate['url']))
                self.handle_exception(e, candidate)
                continue

            if resp.headers.get('content-encoding') == 'gzip':
                gzipped_img = resp.read()
                img_data = gzip.GzipFile(fileobj=StringIO(gzipped_img))
                new_img = img_data.read()
                img_data.close()
            else:
                new_img = resp.read()
            md5 = hashlib.md5(new_img).hexdigest()
            if md5 not in unique_img_hashes:
                img_path = os.path.join(self.output, candidate['filename'])
                f = open(img_path, 'wb')
                f.write(new_img)
                f.close()
                try:
                    Image.open(img_path)
                except IOError, e:
                    self.handle_exception(e, candidate)
                    os.remove(img_path)
                unique_img_hashes.append(md5)
                self.add_to_main_db_table(candidate, md5)
            new += 1
            #only mark posts as handled if the whole run completes,
        # so that galleries can complete if interrupted
        self.add_to_previous_aquisitions()

        for ex in self.exceptions:
            if ex in self.unhandled:
                self.unhandled.remove(ex)

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

        print '\nComplete. %d new images were acquired this run.' % new