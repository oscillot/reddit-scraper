import urllib
import urllib2
import json
import gzip
from StringIO import StringIO
import os
import sys
import sqlite3
from PIL import Image

#Platform agnostic handler for paths
#*NOTE* This assumes that on *nix systems you will install this to the root
# of your user folder
if 'linux' in sys.platform.lower():
    APP_ROOT = os.path.expanduser('~')
elif sys.platform.startswith('win'):
    APP_ROOT = 'C:\\'

#Load an arbitrary umber of arbitrarily named plugins from the plugins folder
plugins_folder = os.path.join(APP_ROOT, 'reddit-scraper', 'plugins')
plugin_list = []
for r, d, f in os.walk(plugins_folder):
    for p in f:
        if p.endswith('.py'):
           plugin_list.append(p.rstrip('.py'))

sys.path.insert(0, plugins_folder)
loaded_plugins = []
failed_plugins = []
for plugin in plugin_list:
    try:
        loaded = __import__(plugin)
        loaded_plugins.append(loaded)
    except ImportError, e:
        print '%s failed to load: %s' % (plugin, e)
        failed_plugins.append(plugin)
sys.path.remove(plugins_folder)

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
        #Create the DB if it's not there
        if not os.path.exists(self.db):
            conn = sqlite3.connect(self.db)
            c = conn.cursor()
            c.execute('''CREATE TABLE wallpapers (subreddit, title, url,
            filename)''')
            conn.commit()
            conn.close()
            

    def login(self):
        """
        Logs in using SSL with the specified credentials,
        retrieves a login cookie for use in future requests. NOTE: Obey
        reddit's API throttling rules! You can't upvote fast enough that you
        would have to break them anyway!
        """
        print 'Logging in...'
        data = urllib.urlencode(
            {'user' : self.username,
             'passwd' : self.password,
             'rem' : 'True'})
        opener = urllib2.build_opener()
        opener.addheaders = [] #remove the default python user-agent
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
        print 'Logged in %s' % self.username
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
            print 'Error in basic request (%s):' % url
            print e
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
            print 'Nothing returned trying to request \"%s\"!' % sub_name
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
            print 'Nothing returned trying to request your subs (mine.json)!'
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
            print 'Nothing returned trying to request your info (me.json)!'
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
                  '.json)!' % self.username
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
        print 'Likes retrieved!'
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
        print 'Getting candidates...'
        for i, sub in enumerate(subs):
            subs[i] = sub.lower()

        children = []
        candidates = []
        for child in liked_data:
            if child['data']['subreddit'].lower() in subs:
                children.append(child)

        #Call each plugin module and hand the list of unhandled links off to
        # it. Plugin *must* return a list of the links that were successfully
        # handled AND a list of candidates where each member of that list is
        # a dictionary with the following keys: 'url', 'subreddit', 'title'
        for plugin in loaded_plugins:
            handled, candidates = plugin.execute(children, candidates)
            #remove handled links here so each plugin doesn't have to do this
            # itself
            for h in handled:
                children.remove(h)

        print 'Candidates retrieved!'

        if len(children) > 0:
            for c in children:
                #inform of any unhandled cases
                #TODO write these to the database
                print 'Unhandled link: %s' % c['data']['url']

        return candidates

    def handle_exception(self, cursor, error, candidate):
        """
        To be called when an exception is caught or raised that prevents the
        image from being acquired. Error is put into the database for use
        later.


        """
        print error
        cursor.execute('''INSERT INTO wallpapers VALUES (?, ?, ?, ?)''',
                       (candidate['subreddit'], candidate['title'],
                       '%s: %s' % (str(e), candidate['url']),
                       candidate['filename']))
        self.existing.append(candidate['filename'])

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
        print 'Getting wallpapers...'
        db_connection = sqlite3.connect(self.db)
        sql_cursor = db_connection.cursor()
        sql_cursor.execute('''SELECT filename FROM wallpapers''')
        self.existing = [f[0] for f in sql_cursor.fetchall()]
        for candidate in candidates:
            candidate['filename'] = candidate['url'].split('/')[-1].replace(
                ' ', '_')
            if candidate['filename'] in self.existing:
                continue
            for key in ['subreddit', 'url', 'title']:
                print candidate[key].encode('ascii','replace')
            print '\n'
            try:
                resp = urllib.urlopen(candidate['url'])
            except urllib2.HTTPError, e:
                self.handle_exception(sql_cursor, e, candidate)
                db_connection.commit()
                continue
            if resp.headers.get('content-type') not in ['image/bmp',
                                                        'image/png',
                                                        'image/jpg',
                                                        'image/jpeg',
                                                        'image/gif']:
                e = ValueError('Image header indicates a non-image was '
                               'found at the link: %s' % candidate['url'])
                self.handle_exception(sql_cursor, e, candidate)
                db_connection.commit()
                continue
            if resp.headers.get('content-encoding') == 'gzip':
                gzipped_img = resp.read()
                img_data = gzip.GzipFile(fileobj=StringIO(gzipped_img))
                new_img = img_data.read()
                img_data.close()
            else:
                new_img = resp.read()
            img_path = os.path.join(output, candidate['filename'])
            f = open(img_path, 'wb')
            f.write(new_img)
            f.close()
            try:
                Image.open(img_path)
            except IOError, e:
                self.handle_exception(sql_cursor, e, candidate)
            sql_cursor.execute('''INSERT INTO wallpapers VALUES (?, ?, ?, ?)''',
                               (candidate['subreddit'], candidate['title'],
                               candidate['url'], candidate['filename']))
            self.existing.append(candidate['filename'])
            db_connection.commit()
        db_connection.close()
        print 'Complete.'