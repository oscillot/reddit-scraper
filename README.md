The reddit-scraper requires lxml. Please install it from lxml.de.
For windows, I used the prebuilt binaries at:
http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

This project was built using lxml 3.02, and Python 2.7.3-2.7.5,
though other versions may work. It also requires requests, sqlalchemy,
pillow and BeautifulSoup4.

HOW TO WRITE PLUGINS
--------------------------------------------------------------------------------
Plugin modules can have any name but must go in the plugins folder
(reddit-scraper/plugins).

The built-in DirectLink plugin should handle most direct links,
so when you a writing a plugin it is likely because something was not handled
by this.

Your plugin must be a class that subclasses BasePlugin from the base_plugin
module in this folder. If it does not subclass this, it will not be executed.

Your plugin needs exactly one function, "execute". Execute is called repeatedly
by the logic in the BasePlugin class, once per Download object in the
CandidateList that has been passed to it. The current Download candidate
object will be the one in the plugin at self.candidate.

A Download object has 5 attributes, 4 of which are set on creation,
along with an optional sixth attribute, which you set if needed:
* title     - this is taken from the reddit post
* subreddit - this is also taken from the reddit post
* url       - this is the url of the POST and not necessarily the IMAGE or
                IMAGES that you want (this is why we are doing this!)
* filename  - this is created automatically by a function that parses the
                url. It does NOT matter if the post is for a multi-image
                gallery because you will be making a new Download object for
                each image in that gallery anyway
* md5       - you set this once you have downloaded the image it's one of
                the last things you do but you still check it against the
                database to avoid duplicate images
* cookies   - you set this attribute as needed if a cookie is necessary for
                the download to complete successfully. It is not necessary to
                set this to None if you do not have a cookie, simply omit it,
                and let the BasePlugin handle it for you.

The approach that I take for writing plugins is typically to have the execute
function call a helper function that returns an img_url (and when needed a
cookie), typically I just drill down the tree with find or find_all using
BeautifulSoup, nothing too fancy, though there are some exceptions.

This important part is to create the self.current object and set it to a
Download object with a valid url and whatever else it may need so that the
BasePlugin can do its work.

For example, for non direct imgur links, it looks like this (abridged):

    class ImgurSingleIndirect(BasePlugin):
        def execute(self, candidate):
            if (candidate.url.lower().startswith('http://imgur.com/'):
                img_url = self.get_imgur_single(candidate.url)
                for album_img in album_imgs:
                    ...
                    self.current = Download(candidate.title,
                                            candidate.subreddit,
                                            img_url)

        def get_imgur_single(self, url):
            ...
            return urls

If you have a gallery, it isn't any more complicated. Just return an iterable
and iterate through the list, setting the self.current object each time
through the loop. self.current is a property that has a setter. If it is not
set to None, the acquisition logic is triggered so you can set the object as
few or as many times as you want from within execute and the logic to acquire
the image will still fire off each time you set the object.

    class ImgurAlbum(BasePlugin):
        def execute(self, candidate):
            if candidate.url.lower().startswith('http://imgur.com/a/'):
                album_imgs = self.get_imgur_album(candidate.url)
                for album_img in album_imgs:
                    ...
                    self.current = Download(candidate.title,
                                            candidate.subreddit,
                                            album_img_url)

        def get_imgur_album(self, url):
            ...
            return urls

NOTES: It is recommended to set PYTHONUNBUFFERED=1 when running in Jenkins so
 that the console updates in something closer to real-time,
 otherwise trying to watch the console pretty much sucks.