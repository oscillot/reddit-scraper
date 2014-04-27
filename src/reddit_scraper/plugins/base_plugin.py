import os
import time
import hashlib
import traceback

from PIL import Image
import requests
from requests.exceptions import HTTPError
from sqlalchemy import *
import sqlalchemy.sql as sql

from reddit_scraper.data_types import CandidatesList, DownloadList, Download
from reddit_scraper.util import ensure_ascii


IMAGE_HEADERS = ['image/bmp',
                 'image/png',
                 'image/jpg',
                 'image/jpeg',
                 'image/gif']


class BasePlugin(object):
    def __init__(self, database, candidates, output, categorize=False,
                 nsfw=False):
        """The BasePlugin class actually does all of the work under the hood.
        It creates the database, performs the database calls. Retrieves images
        from content servers, does any error handling that plugins neglect to
        do and outputs it without bombing the whole job out.

        :param str database: the prefix for the database filename.
        :param list candidates: a list of candidate json objects from the
        `class` RedditConnect class
        :param str output: the location on disk to store your images (note
        that this can be changed and the database data will handle all
        duplicate filtering
        :param bool categorize: whether to create subfolders of the subreddit
        names where images came from. Defaults to False.
        """
        self.date = str(int(time.time()))
        self.candidates = candidates
        self.candidates_backup = None
        self.revised = None
        self.output_dir = output
        self.categorize = categorize
        self.nsfw = nsfw
        self.to_acquire = []
        self.handled_posts = {}
        self.unhandled_posts = set()
        self.db = os.path.join(os.getcwd(), '%s_downloaded.db' % database)
        self.engine = create_engine('sqlite:///%s' % self.db)
        metadata = MetaData(self.engine)
        self.wallpapers = Table('wallpapers', metadata,
                                Column('date', String),
                                Column('subreddit', String),
                                Column('title', String),
                                Column('url', String),
                                Column('filename', String),
                                Column('md5', String, primary_key=True))
        #Create the DB tables if not there
        metadata.create_all()
        self.unique_img_hashes = self.get_previous_md5s()
        self._current = None
        self.enforcer()

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        if value is not None:
            self.acquisition_tasks()

        else:
            self.unhandled_posts.add(self.candidate)

    def acquisition_tasks(self):
        if self.current.url in self.image_urls_already_fetched:
            #skip any exact url matches from the db
            print '%s: Skipping url %s: already downloaded\n' % \
                  (self.__class__.__name__, self.current.url)
        else:
            #print data about the current acquisition
            print '%s: Requesting: %s \n' % \
                  (self.__class__.__name__, self.current.url)

            #snag the image! woot! that's what it all leads up to
            # in the end!
            try:
                #use the cookie if we have one
                if hasattr(self.current, 'cookies') and \
                        self.current.cookies is not None:
                    self.resp = requests.get(self.current.url,
                                             cookies=self.current.cookies)
                else:
                    self.resp = requests.get(self.current.url)
            except HTTPError, e:
                #or abject failure, you know, whichever...
                print '%s: Failure: %s \n' % \
                      (self.__class__.__name__, e.message)
                self.current = None

            #maybe we got very close, or an image got removed, in any case
            # MAKE SURE IT'S AN IMAGE!
            if not self.valid_image_header():
                e = ValueError('Non-image header \"%s\" was found at the '
                               'link: %s' %
                               (self.resp.headers.get('content-type'),
                                self.current.url))
                print e.message
                self.unhandled_posts.add(self.candidate)
                self.current = None
            else:
                #finally! we have image!
                new_img = self.resp.content
                self.current.md5 = hashlib.md5(new_img).hexdigest()
                if self.candidate not in self.handled_posts.keys():
                    self.handled_posts[self.candidate] = set()

                if self.current.md5 not in self.unique_img_hashes:
                    self.handled_posts[self.candidate].add(self.current)
                    self.save_img(new_img)
                    self.unique_img_hashes.add(self.current.md5)
                    self.add_to_main_db_table()
                    # self.add_to_previous_aquisitions()
                    print '%s: Success! %s saved.\n' % \
                          (self.__class__.__name__, '%s: %s' % (
                              ensure_ascii(self.current.title),
                              self.current.filename))
                else:
                    self.current.duplicate = True
                    self.handled_posts[self.candidate].add(self.current)
                    print '%s: MD5 duplicate. Discarding: %s.\n' % \
                          (self.__class__.__name__, '%s: %s' % (
                              ensure_ascii(self.current.title),
                              self.current.filename))
                #remove successes so the whole run goes faster
                self.revised.remove(self.candidate)

    def add_to_main_db_table(self):
        """
        Inserts the full handled link info into the wallpapers table of the db
        """
        conn = self.engine.connect()
        wall_data = (self.date, self.current.subreddit, self.current.title,
                     self.current.url, self.current.filename, self.current.md5)
        wall_ins = self.wallpapers.insert(wall_data)
        conn.execute(wall_ins)

    def check_db_for_finished_image_urls(self):
        """
        Returns a `class` DownloadList of urls that has successfully been
        downloaded. This helps make sure that if a gallery post is picked up
        partway that we don't re-attempt the first already fetched posts as
        well as for skipping already fetched single image posts.
        """
        conn = self.engine.connect()
        finished_urls_select = sql.select([self.wallpapers])
        self.image_urls_already_fetched = DownloadList(
            set(a[2] for a in conn.execute(
                finished_urls_select).fetchall()))

    def convert_candidates(self):
        """
        This converts the candidates list from the generic list of
        dictionaries that came from the `class` RedditConnect json data into
        the internal CandidateList data format which contains only the
        necessary information and makes the code much easier to read and
        understand
        """
        if type(self.candidates) == CandidatesList:
            self.candidates_backup = self.candidates
            self.revised = self.candidates
            return
        else:
            new_cands = set()
            for c in self.candidates:
                new_cands.add(Download(c['data']['title'],
                                       c['data']['subreddit'],
                                       c['data']['url'],
                                       c['data']['over_18']))
            self.candidates = CandidatesList(new_cands)
            self.candidates_backup = self.candidates
            self.revised = self.candidates

    def enforcer(self):
        """
        The enforcer is a hidden executor that handles iterating through the
        list of links and catching any unexpected exceptions thrown by the
        plugin gracefully, reporting the plugin, link and exception output as
        the run progresses
        """
        #Convert candidates from the generic format provided by my Reddit
        # connect class to something specific with only the necessary
        # attributes needed for downloading images
        self.convert_candidates()
        #create self.already_dled
        self.check_db_for_finished_image_urls()
        #remove the above, if found, from the returned list before doing
        # anything
        self.prune()
        for candidate in self.candidates:
            #check the NSFW flag for filtering
            if not self.nsfw and candidate.nsfw:
                print 'Skipping NSFW Image: %s' % self.candidate.url
                continue
            #make the candidate object easily available everywhere
            self.candidate = candidate
            #reset the Download object to None on each iteration of the loop
            self.current = None
            try:
                #this creates a Download object at self.current
                self.execute()
            except Exception, e:
                print traceback.print_exc()
                self.unhandled_posts.add(self.candidate)
            #     continue
            # #EXPERIMENTAL:
            # self.add_to_previous_aquisitions()

    def execute(self):
        """
        To be overridden by subclasses. The subclassed versions of this
        method should be written to handle just one post link,
        but can call other functions as needed. See the plugin readme on how
        this should be done.
        """
        raise NotImplementedError

    @staticmethod
    def url_matches(url):
        """
        To be overridden by subclasses. The subclassed versions of this
        method should be a regex takes self.candidate.url and returns True if
        the plugin should attempt it or False if the plugin should not.

        This MUST be a @staticmethod
        """
        raise NotImplementedError

    def get_previous_md5s(self):
        """
        Returns the list of md5s already in the database
        """
        conn = self.engine.connect()
        md5_select = sql.select(from_obj=self.wallpapers, columns=['md5'])
        unique_img_hashes = set(h[0] for h in
                                conn.execute(md5_select).fetchall())
        return unique_img_hashes

    def prune(self):
        """
        Remove anything from the new `class` CandidatesList that is found in
        the database from the beginning, try to be as econmoical as possible
        and avoid getting ip or other form of blacklisted at all costs
        """
        self.candidates.difference(self.image_urls_already_fetched.downloads)

    def save_img(self, data):
        """
        What it sounds like. Code responsible for saving off the image to the
        filesystem and display any errors that might arise
        """
        #Move the logic that strips url args here in case they were needed for
        # downloads (was stripping it before acquisition like a total noob)
        if '?' in self.current.filename:
            self.current.filename = self.current.filename.split('?')[0]
        #Add the subfolders conditionally:
        if self.categorize:
            category_dir = os.path.join(self.output_dir,
                                        self.current.subreddit)
            #since this is a subfolder, it may not yet exist!
            if not os.path.exists(category_dir):
                os.makedirs(category_dir)
        else:
            category_dir = self.output_dir
        #Add the output path to the filename
        orig_img_path = os.path.join(category_dir, self.current.filename)
        #handle incrementing the image name with a number if we pass the MD5
        # but the filename was taken
        #the original image path is the INTENDED image path, the img_path is
        # what it ends up being if there is a namespace collision on the
        # filesystem
        img_path = orig_img_path

        orig_path, orig_ext = orig_img_path.rsplit('.', 1)
        inc = 1
        #prevent stupidly named files like image.jpg from being overwritten
        # all the time
        while os.path.exists(img_path):
            img_path = '%s_%d.%s' % (orig_path, inc, orig_ext)
            inc += 1
        with open(img_path, 'wb') as f:
            f.write(data)
        try:
            Image.open(img_path)
        except IOError:
            print traceback.print_exc()
            os.remove(img_path)

    def valid_image_header(self):
        """
        This checks the response header for the content type so we aren't
        saving bunk data into a file and calling it an image. This happens a
        lot especially with sites that try not to let you scrape them for
        their high quality images, so it's an important check.
        """
        for header in IMAGE_HEADERS:
            #this handles headers that look like this:
            #image/jpeg; charset=UTF-8
            if header in self.resp.headers.get('content-type'):
                return True
        #if we get here no header matched
        return False