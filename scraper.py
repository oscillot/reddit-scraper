import urllib, urllib2, json, gzip
from StringIO import StringIO
import os, sys
import sqlite3
import imp
from lxml import etree

if 'linux' in sys.platform.lower():
    APP_ROOT = os.path.expanduser('~')
elif sys.platform.startswith('win') or sys.platform == 'cli':
    APP_ROOT = 'C:\\'

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

def pretty_print(data, delimiter):
    if type(data) not in [str, unicode]:
        data = unicode(data)
    print data.replace('%s' % delimiter, '%s\n' % delimiter)
    print '\n'

class RedditConnect():
    def __init__(self, username, password, database):
        self.user = username
        self.passwd = password
        self.db = os.path.join(os.getcwd(),'%s_downloaded.db' % database)
        if not os.path.exists(self.db):
            conn = sqlite3.connect(self.db)
            c = conn.cursor()
            c.execute('''CREATE TABLE wallpapers (subreddit, title, url, filename)''')
            conn.commit()
            conn.close()
            

    def login(self):
        """
        Logs in with the specified credentials, retrieves a login cookie for use in future requests. NOTE: Obey
        reddit's API throttling rules! You can't upvote fast enough that you would have to break them anyway!
        """
        print 'Logging in...'
        data = urllib.urlencode(
            {'user' : self.user,
             'passwd' : self.passwd,
             'rem' : 'True'})
        opener = urllib2.build_opener()
        opener.addheaders = [] #remove the default python user-agent
        opener.addheaders.append(('User-agent', 'Downloader for /user/%s\'s upvoted images in specified subreddits by /user/oscillot' % self.user))
        urllib2.install_opener(opener)
        resp = urllib2.urlopen('https://ssl.reddit.com/api/login/%s?' % self.user, data)
        json_str =  resp.read()
        json_resp = json.loads(json_str)
        self.cookie = resp.headers.get('set-cookie')
        opener.addheaders.append(('Cookie', self.cookie))
        urllib2.install_opener(opener)
        print 'Logged in %s' % self.user

    def basic_request(self, url):
        resp = urllib2.urlopen(url)
        return resp.read()

    def get_sub(self, sub_name):
        the_page = self.basic_request('http://www.reddit.com/r/%s.json' % sub_name)
        return the_page

    def get_my_subs(self):
        the_page = self.basic_request('http://www.reddit.com/reddits/mine.json')
        return the_page

    def get_about_me(self):
        the_page = self.basic_request('http://www.reddit.com/api/me.json')
        return the_page

    def get_liked(self, max_pages=1):
        print 'Retrieving likes...'
        total_liked_data = []
        liked_json = self.basic_request('http://www.reddit.com/user/%s/liked.json' % self.user)
        json_data = json.loads(liked_json)
        total_liked_data += json_data['data']['children']
        if max_pages > 1:
            for r in range(1, max_pages+1):
                liked_json = self.basic_request('http://www.reddit.com/user/%s/liked.json?count=%d&after=%s' % (self.user, r*25, json_data['data']['after']))
                json_data = json.loads(liked_json)
                total_liked_data += json_data['data']['children']
        print 'Likes retrieved!'
        return total_liked_data

    def get_upvoted_wallpapers(self, subs, liked_data):
        print 'Getting candidates...'
        for i, sub in enumerate(subs):
            subs[i] = sub.lower()

        children = []
        candidates = []
        for child in liked_data:
            if child['data']['subreddit'].lower() in subs:
                children.append(child)

        #Call each plugin module and hand the list of unhandled links off to it.
        #plugin *must* return a list of the links that were successfully handled AND
        # a list of candidates where each member of that list is a dictionry with the following keys:
        #'url', 'subreddit', 'title'
        for plugin in loaded_plugins:
            handled, candidates = plugin.execute(children, candidates)
            for h in handled:
                children.remove(h)

        print 'Candidates retrieved!'

        if len(children) > 0:
            for c in children:
                #inform of any unhandled cases
                #TODO write these to the database
                print 'Unhandled link: %s' % c['data']['url']

        return candidates

    def acquire(self, candidates, output):
        print 'Getting wallpapers...'
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute('''SELECT filename FROM wallpapers''')
        existing = [f[0] for f in c.fetchall()]
        for cand in candidates:
            filename = cand['url'].split('/')[-1].replace(' ', '_')
            if filename in existing:
                continue
            for key in ['subreddit', 'url', 'title']:
                print cand[key].encode('ascii','replace')
            print '\n'
            try:
                resp = urllib.urlopen(cand['url'])
                if resp.headers.get('content-encoding') == 'gzip':
                    gzipped_img = resp.read()
                    img_data = gzip.GzipFile(fileobj=StringIO(gzipped_img))
                    new_img = img_data.read()
                    img_data.close()
                else:
                    new_img = resp.read()
            except urllib2.HTTPError as e:
                print e
                c.execute('''INSERT INTO wallpapers VALUES (?, ?, ?, ?)''', (cand['subreddit'], cand['title'], '%s: %s' % (e, cand['url']), filename))
                existing.append(filename)
                conn.commit()
                continue
            f = open(os.path.join(output, filename), 'wb')
            f.write(new_img)
            f.close()
            c.execute('''INSERT INTO wallpapers VALUES (?, ?, ?, ?)''', (cand['subreddit'], cand['title'], cand['url'], filename))
            existing.append(filename)
            conn.commit()
        conn.close()
        print 'Complete.'