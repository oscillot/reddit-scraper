import time
import json

import requests


class RedditConnect():
    """
    Constructor for the connection. Sets up the variables for the SSL
    connection as well as the sqlite database.

    :param str username: The reddit username
    :param str password: The password for above username
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.headers = {'User-agent': 'Downloader for /user/%s\'s upvoted '
                                      'images in specified subreddits by '
                                      '/user/oscillot' % self.username}
        self.cookie = None

    def login(self):
        """
        Logs in using SSL with the specified credentials,
        retrieves a login cookie for use in future requests. NOTE: Obey
        reddit's API throttling rules! You can't upvote fast enough that you
        would have to break them anyway!
        """
        print 'Logging in...'
        data = {'user': self.username,
                'passwd': self.password,
                'rem': 'True'}

        try:
            resp = requests.post('https://ssl.reddit.com/api/login/%s?' %
                                 self.username, data, headers=self.headers)
        except requests.HTTPError, e:
            print 'Error contacting reddit:'
            raise e
        json_str = resp.text
        json_resp = json.loads(json_str)

        self.cookie = dict(resp.cookies.items())
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
            resp = requests.get(url, headers=self.headers,
                                cookies=self.cookie)
        except requests.HTTPError, e:
            print 'Error in basic request (%s): %s\n' % (url, e)
            return
        return resp.text

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

    def get_upvotes(self, max_pages=1):
        """
        Get the json listing of the user's upvoted posts. Must be logged in
        and cookied for this to work!

        :param int max_pages: How many pages of liked data to parse. 1 page =
         25 posts.
        :returns list: A list of dictionaries converted from the json response
        """
        print 'Retrieving upvotes...'
        total_upvoted_data = []
        upvoted_json = self.basic_request('http://www.reddit.com/user/%s/liked'
                                          '.json' % self.username)
        if upvoted_json is None:
            print 'Nothing returned trying to request your upvotes (%s/liked' \
                  '.json)!\n' % self.username
            raise ValueError
        json_data = json.loads(upvoted_json)
        total_upvoted_data += json_data['data']['children']
        print '1 Page Processed: %d Upvotes Found So Far...' % \
              len(total_upvoted_data)
        if max_pages > 1:
            for r in range(1, max_pages + 1):
                try:
                    upvoted_json = self.basic_request('http://www.reddit'
                                                      '.com/user/%s/liked'
                                                      '.json?count=%d&after=%s'
                                                      % (self.username, r * 25,
                                                      json_data['data']
                                                      ['after']))
                except requests.exceptions.ConnectionError, e:
                    if len(total_upvoted_data) > 0:
                        print 'WARNING: Connection error!'
                        print e
                        print 'Upvotes only partially retrieved.'
                        return total_upvoted_data
                    else:
                        raise e
                json_data = json.loads(upvoted_json)
                total_upvoted_data += json_data['data']['children']
                print '%d Pages Processed: %d Upvotes Found So Far...' % \
                      (r + 1, len(total_upvoted_data))
                self.wait()
        print 'Upvotes retrieved!\n'
        return total_upvoted_data

    def get_upvoted_wallpapers(self, subs, liked_data):
        """
        Get the urls for upvotes in a specific subset of subreddits. This is
        the list of candidate upvotes from which we try to extract an
        actionable url to either download directly from or we pass to a
        plugin for the purpose or parsing and eventual odwnload link
        extraction.
        :param list subs: A list of strings naming each subreddit to get
        images from.

        :param list liked_data: the list of dictionaries returned from :func:
        get_upvotes. The 'url' key of these dictionaries can go to any webpage
        but need an explicit handler for albums or to parse non-direct links.
         See the included plugins for examples.
        :returns list: A list of dictionaries where each key 'url' is a
        direct link to an image
        """
        print 'Getting candidates...\n'
        for i, sub in enumerate(subs):
            subs[i] = sub.lower()

        candidates = []
        for child in liked_data:
            if child['data']['subreddit'].lower() in subs:
                candidates.append(child)
        return candidates

    def wait(self):
        """
        Waits two seconds whenever the API agreement decrees that you must
        wait. This prevents the bot from getting blocked and having requests
        sit around for the max timeout, the effects of which are worse on
        large jobs which is usually when this happens anyway.

        https://github.com/reddit/reddit/wiki/API#rules
        """
        time.sleep(2)