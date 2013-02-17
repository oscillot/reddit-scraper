import urllib
import urllib2
import json
import gzip
from StringIO import StringIO
import os
import sys
import hashlib

from sqlalchemy import *
import sqlalchemy.sql as sql
from PIL import Image

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
        loaded_plugins.append(loaded)
        succeeded.append(plugin)
    except ImportError, e:
        print '%s failed to load: %s\n' % (plugin, e)
        failed_plugins.append(plugin)
sys.path.remove(plugins_folder)
print 'Loaded the following plugin modules successfully: %s\n' % ', '.join(
    succeeded)

class RedditConnect():
    """
    Constructor for the connection. Sets up the variables for the SSL
    connection as well as the sqlite database.

    :param str username: The reddit username
    :param str password: The password for above username
    :param str database: The prefix for the database name for %s_downloaded.db
    """
    #TODO: Consider using SQLAlchemy to make this less ugly
    def __init__(self, username, password, database):
        self.username = username
        self.password = password
        self.db = os.path.join(os.getcwd(),'%s_downloaded.db' % database)
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
        self.unhandled = []

    def login(self):
        """
        Logs in using SSL with the specified credentials,
        retrieves a login cookie for use in future requests. NOTE: Obey
        reddit's API throttling rules! You can't upvote fast enough that you
        would have to break them anyway!
        """
        print 'Logging in...'
        data = urllib.urlencode(
            {'user': self.username,
             'passwd': self.password,
             'rem': 'True'})
        opener = urllib2.build_opener()
        opener.addheaders = []  # remove the default python user-agent
        opener.addheaders.append(('User-agent', 'Downloader for /user/%s\'s '
                                                'upvoted images in specified '
                                                'subreddits by '
                                                '/user/oscillot' % self.username))
        urllib2.install_opener(opener)
        try:
            resp = urllib2.urlopen('https://ssl.reddit.com/api/login/%s?' %
                                   self.username, data)
        except urllib2.HTTPError, e:
            print 'Error contacting reddit:'
            raise e
        json_str = resp.read()
        json_resp = json.loads(json_str)
        self.cookie = resp.headers.get('set-cookie')
        opener.addheaders.append(('Cookie', self.cookie))
        urllib2.install_opener(opener)
        print 'Logged in as %s\n' % self.username
        return json_resp

    def basic_request(self, url):
        """
        Initiate a basic get request using the opener created and cookie
        retrieved in :func: login or the default opener if login hasn't been
        called yet. Convenience for other pointed requests.

        :param str url: the url to get
        :returns str: the read response
        """
        try:
            resp = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            print 'Error in basic request (%s): %s\n' % (url, e)
            return
        return resp.read()

    def get_sub(self, sub_name):
        """
        Get the JSON stream for a particular subreddit.

        :param str sub_name: The name of the subreddit
        :returns str: The response if successful.
        """
        the_page = self.basic_request('http://www.reddit.com/r/%s.json' %
                                      sub_name)
        if the_page is None:
            print 'Nothing returned trying to request \"%s\"!\n' % sub_name
            raise ValueError
        return the_page

    def get_my_subs(self):
        """
        Get the json listing of my subscribed subreddits. Must be logged in
        and cookied for this to work!

        :returns str: The response if successful.
        """
        the_page = self.basic_request('http://www.reddit.com/reddits/mine.json')
        if the_page is None:
            print 'Nothing returned trying to request your subs (mine.json)!\n'
            raise ValueError
        return the_page

    def get_about_me(self):
        """
        Get the json listing of my the user's about page. Must be logged in
        and cookied for this to work!

        :returns str: The response if successful.
        """
        the_page = self.basic_request('http://www.reddit.com/api/me.json')
        if the_page is None:
            print 'Nothing returned trying to request your info (me.json)!\n'
            raise ValueError
        return the_page

    def get_liked(self, max_pages=1):
        """
        Get the json listing of the user's liked posts. Must be logged in
        and cookied for this to work!

        :param int max_pages: How many pages of liked data to parse. 1 page =
         25 posts.
        :returns list: A list of dictionaries converted from the json response
        """
        print 'Retrieving likes...'
        total_liked_data = []
        liked_json = self.basic_request('http://www.reddit.com/user/%s/liked'
                                        '.json' % self.username)
        if liked_json is None:
            print 'Nothing returned trying to request your likes (%s/liked' \
                  '.json)!\n' % self.username
            raise ValueError
        json_data = json.loads(liked_json)
        total_liked_data += json_data['data']['children']
        if max_pages > 1:
            for r in range(1, max_pages+1):
                liked_json = self.basic_request('http://www.reddit'
                                                '.com/user/%s/liked'
                                                '.json?count=%d&after=%s' % (
                                                self.username, r * 25,
                                                json_data['data']['after']))

                json_data = json.loads(liked_json)
                total_liked_data += json_data['data']['children']
        print 'Likes retrieved!\n'
        return total_liked_data

    def get_upvoted_wallpapers(self, subs, liked_data):
        """
        Get the urls for likes in a specific subset of subreddits
        :param list subs: A list of strings naming each subreddit to get
        images from.

        :param list liked_data: the list of dictionaries returned from :func:
        get_liked. The 'url' key of these dictionaries can go to any webpage
        but need an explicit handler for albums or to parse non-direct links.
         See the included plugins for examples.
        :returns list: A list of dictionaries where each key 'url' is a
        direct link to an image
        """
        print 'Getting candidates...\n'
        for i, sub in enumerate(subs):
            subs[i] = sub.lower()

        children = []
        candidates = []
        already_handled = self.list_previous_handled_posts()
        for child in liked_data:
            if child['data']['subreddit'].lower() in subs:
                if child['data']['url'] not in already_handled:
                    already_handled.append(child['data']['url'])
                    children.append(child)
                else:
                    print 'Skipping previously acquired post: %s' % child[
                        'data']['title']

        #Call each plugin module and hand the list of unhandled links off to
        # it. Plugin *must* return a list of the links that were successfully
        # handled AND a list of candidates where each member of that list is
        # a dictionary with the following keys: 'url', 'subreddit', 'title'
        self.handled = []
        for plugin in loaded_plugins:
            print 'Loading plugin: %s.\n' % plugin
            handled, candidates = plugin.execute(children, candidates)
            self.handled.extend(handled)
            print 'Plugin handled the following links:'
            for h in handled:
                print h['data']['url']
            print '\n'
            #remove handled links here so each plugin doesn't have to do this
            # itself
            for h in handled:
                children.remove(h)

        print 'Candidates retrieved!\n'

        if len(children) > 0:
            for c in children:
                #inform of any unhandled cases
                self.unhandled.append(c['data']['url'])

        return candidates

    def handle_exception(self, error, candidate):
        """
        To be called when an exception is caught or raised that prevents the
        image from being acquired. Error is put into the database for use
        later. After 5 errors the link is no longer tried.
        """
        print '%s\n' % str(error)
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
                                                             old_attempts + 1})
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
        already_handled = [a[0] for a in conn.execute(retrieved_select)
        .fetchall()]
        return already_handled

    def list_handled_image_links(self):
        """
        Returns the ist of urls that has successfully been handled.
        """
        conn = self.engine.connect()
        retrieved_select = sql.select([self.wallpapers])
        already_dled = [a[2] for a in conn.execute(retrieved_select)
                        .fetchall()]
        return already_dled

    def add_to_previous_aquisitions(self, handled):
        """
        Adds to the list of previously handled links
        """
        for h in handled:
            conn = self.engine.connect()
            retrieved_ins = sql.insert(table=self.retrieved,
                                       values=[h['data']['url']])
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

    def acquire(self, candidates, output):
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
        if not os.path.exists(output):
            os.makedirs(output)
        new = 0
        print 'Found %d candidates.\n' % len(candidates)
        print 'Getting wallpapers...\n'
        unique_img_hashes = self.get_previous_md5s()
        total = len(candidates)
        for i, candidate in enumerate(candidates):
            candidate['filename'] = candidate['url'].split('/')[-1].replace(
                ' ', '_')
            already_dled = self.list_handled_image_links()
            if candidate['url'] in already_dled:
                print 'Skipping #%d/%d: %s has already been downloaded\n' % (
                    i, total, candidate['filename'])
                continue
            if self.too_many_error_attempts(candidate):
                print 'Skipping #%d/%d: %s has failed 5 or more times\n' % (
                    i, total, candidate['filename'])
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
                e = ValueError('Image header indicates a non-image was '
                               'found at the link: %s' % candidate['url'])
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
                img_path = os.path.join(output, candidate['filename'])
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
        self.add_to_previous_aquisitions(self.handled)

        print 'The following posts had links that were unhandled:'
        for uh in self.unhandled:
            print uh
        print '\nComplete. %d new images were acquired this run.' % new