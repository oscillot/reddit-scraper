import os
import hashlib
import traceback

from PIL import Image
import requests
from sqlalchemy import *
import sqlalchemy.sql as sql

IMAGE_HEADERS = ['image/bmp',
                 'image/png',
                 'image/jpg',
                 'image/jpeg',
                 'image/gif']


class BasePlugin():
    def __init__(self, database, candidates, output):
        """Constructs the plugin calls and executes them, saving successes,
        failures and links as class attributes

        :param list candidates: a list of dictionaries converted from the json
        response given back by reddit.
        :rtype list, list: a list of the dictionary data that was successfully
        parsed by this plugin, a list of dictionaries with the url,
        subreddit and title of the direct link for later acquisition and database
         entry
        """
        self.candidates = candidates
        self.output_dir = output
        self.to_acquire = []
        self.handled = []
        self.unhandled = []
        self.db = os.path.join(os.getcwd(), '%s_downloaded.db' % database)
        self.engine = create_engine('sqlite:///%s' % self.db)
        metadata = MetaData(self.engine)
        self.wallpapers = Table('wallpapers', metadata,
                                Column('subreddit', String),
                                Column('title', String),
                                Column('url', String),
                                Column('filename', String),
                                Column('md5', String, primary_key=True))
        self.retrieved = Table('retrieved', metadata,
                               Column('image_url', String,
                                      primary_key=True))
        #Create the DB tables if not there
        metadata.create_all()
        self.unique_img_hashes = self.get_previous_md5s()
        self.enforcer()

    def enforcer(self):
        """
        This hidden executor handles iterating through the list of links and
        catching any unexpected exceptions thrown by the plugin gracefully,
        reporting the plugin, link and exception for output at the end of the
         run
        """
        self.convert_candidates()
        ##WHY ARE THERE TWO OF THESE YOU MORON??
        #create self.already_dled
        self.check_db_for_already_dled()
        #create self.already_handled
        self.check_db_for_already_handled()
        self.early_prune()
        total = len(self.candidates)
        for i, candidate in enumerate(self.candidates):
            #reset the Download object to None on each iteration of the loop
            self.current = None
            try:
                #this creates a Download object at self.current (or loops
                # around)
                self.execute(candidate)
                #iterate when the plugin returns None
                if not self.current:
                    print 'Skipping #%d/%d: ' \
                          '%s was not handled by %s\n' % \
                          (i + 1, total, candidate.url,
                           self.__class__.__name__)
                    continue
            except Exception, e:
                print traceback.print_exc()
                self.unhandled.append(candidate)
            else:
                if self.current.url not in self.already_handled:
                    ##WHY DO I DO THIS?
                    ###WTF DOUBLE NEGATIVE???
                    self.already_handled.append(self.current.url)
                else:
                    print 'Skipping previously acquired post: ' \
                          '%s' % self.current.url
                    continue

                if self.current.url in self.already_dled:
                    #skip any exact url matches from the db
                    print 'Skipping #%d/%d: ' \
                          '%s has already been downloaded\n' % \
                          (i + 1, total, self.current.filename)
                    continue
                else:
                    #print data about the current acquisition
                    print 'Acquiring #%d/%d: ' \
                          '%s \n' % \
                          (i + 1, total, self.current.filename)
                    print self.current.title.encode('ascii', 'replace'),
                    self.current.subreddit.encode('ascii', 'replace'),
                    self.current.url.encode('ascii', 'replace'), \
                    '\n'

                    try:
                        #snag the image! woot! that's what it all leads up to
                        # in the end!
                        self.resp = requests.get(self.current.url)
                    except requests.HTTPError:
                        #or abject failure, you know, whichever...
                        self.unhandled.append(candidate)
                        continue

                    if not self.valid_image_header():
                        continue
                    else:
                        #finally! we have image!
                        new_img = self.resp.content
                    self.current.md5 = hashlib.md5(new_img).hexdigest()
                    if self.current.md5 not in self.unique_img_hashes:
                        self.save_img(new_img)
                        self.unique_img_hashes.append(self.current.md5)
                        self.add_to_main_db_table()
                        self.revised.remove(candidate)
                        self.handled.append(candidate)

    def convert_candidates(self):
        new_cands = []
        for c in self.candidates:
            if c.__class__.__name__ == 'Download':
                new_cands.append(c)
            else:
                new_cands.append(Download(c['data']['title'],
                                          c['data']['subreddit'],
                                          c['data']['url']))
        self.candidates = CandidatesList(new_cands)
        self.candidates_backup = self.candidates
        self.revised = self.candidates

    def save_img(self, data):
        img_path = os.path.join(self.output_dir, self.current.filename)
        with open(img_path, 'wb') as f:
            f.write(data)
        try:
            Image.open(img_path)
        except IOError:
            print traceback.print_exc()
            os.remove(img_path)

    def valid_image_header(self):
        if self.resp.headers.get('content-type') not in IMAGE_HEADERS:
            #or maybe we got very close, or an image got removed,
            # in any case MAKE SURE IT'S AN IMAGE!
            err = ValueError('Non-image header \"%s\" was found at the link: '
                             '%s' % (self.resp.headers.get('content-type'),
                                     self.current.url))
            print err
            return False
        else:
            return True

    def execute(self, candidate):
        """
        To be overridden by subclasses. The subclassed versions of this
        method should be written to handle just one post link,
        but can call other functions as needed.
        """
        raise NotImplementedError

    def get_previous_md5s(self):
        """
        Returns the list of md5s already in the database
        """
        conn = self.engine.connect()
        md5_select = sql.select(from_obj=self.wallpapers, columns=['md5'])
        unique_img_hashes = [h[0] for h in conn.execute(md5_select).fetchall()]
        return unique_img_hashes

    def check_db_for_already_handled(self):
        """
        Returns the list of previous liked posts that successfully went all
        the way through the scraper
        """
        conn = self.engine.connect()
        retrieved_select = sql.select([self.retrieved])
        self.already_handled = DownloadList([a[0] for a in conn.execute(
                                            retrieved_select).fetchall()])

    def check_db_for_already_dled(self):
        """
        Returns the list of urls that has successfully been downloaded.
        """
        conn = self.engine.connect()
        handled_select = sql.select([self.wallpapers])
        self.already_dled = DownloadList([a[2] for a in conn.execute(
                                         handled_select).fetchall()])

    def add_to_previous_aquisitions(self):
        """
        Adds to the list of previously handled links
        """
        #prevent hash collision in the table
        uniques = set()
        for h in self.handled:
            if h.url not in self.already_handled:
                uniques.add(h.url)
        for u in uniques:
            conn = self.engine.connect()
            retrieved_ins = sql.insert(table=self.retrieved,
                                       values=[u])
            conn.execute(retrieved_ins)

    def add_to_main_db_table(self):
        """
        Inserts the full handled link info into the wallpaers table of the db
        """
        conn = self.engine.connect()
        wall_data = (self.current.subreddit, self.current.title,
                     self.current.url, self.current.filename, self.current.md5)
        wall_ins = self.wallpapers.insert(wall_data)
        conn.execute(wall_ins)

    def early_prune(self):
        print 'already dled'
        print self.already_dled.downloads
        print 'already handled'
        print self.already_handled.downloads
        print 'candidates'
        print self.candidates
        for already in self.already_dled.downloads:
            if already in self.candidates:
                self.candidates.remove(already)
                continue
        for handled in self.already_handled.downloads:
            if handled in self.candidates:
                self.candidates.remove(handled)
                continue


class Download(object):
    def __init__(self, title, subreddit, url):
        self.title = title
        self.subreddit = subreddit
        self.url = url
        self.filename = self.name_from_url()
        self.md5 = None

    def name_from_url(self):
        return self.url.split('/')[-1].replace(' ', '_')


class DownloadList(object):
    def __init__(self, downloads):
        self.downloads = downloads

    def __contains__(self, item):
        for dl in self.downloads:
            if dl.title == item.title and \
                dl.subreddit == item.subreddit and \
                    dl.url == item.url:
                        return dl

    def append(self, item):
        self.downloads.append(item)


class CandidatesList(object):
    def __init__(self, candidates):
        self.candidates = candidates

    def __contains__(self, item):
        for c in self.candidates:
                if item == c.url:
                    return item
        #return item in self.candidates

    def remove(self, item):
        for c in self.candidates:
            print '==='
            print c.url
            print item
            if c.url == item:
                return self.candidates.remove(c)

    def __len__(self):
        return len(self.candidates)

    def __iter__(self):
        for c in self.candidates:
            yield c