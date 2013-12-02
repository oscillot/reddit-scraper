The reddit-scraper requires lxml. Please install it from lxml.de.
For windows, I used the prebuilt binaries at:
http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

This project was built using lxml 3.02, and Python 2.7.3-2.7.5,
though other versions may work. It also requires requests, sqlalchemy and
pillow.

HOW TO WRITE PLUGINS
--------------------------------------------------------------------------------
Plugin modules can have any name but must go in the plugins folder
(reddit-scraper/plugins).

The built-in DirectLink plugin should handle most direct links,
so when you a writing a plugin it is likely because something was not handled
by this.

Your plugin must be a class that subclasses BasePlugin from the base_plugin
module in this folder. If it does not subclass this, it will not be executed.

Your plugin needs exactly one function, "execute". It must accept one positional
argument that will be a single candidate that will be a Download object.
Execute is called repeatedly by the logic in the BasePlugin class, once per
Download object in the CandidateList that has been passed to it.

A Download object has 5 attributes, 4 of which are set on creation:
    title     - this is taken from the reddit post
    subreddit - this is also taken from the reddit post
    url       - this is the url of the POST and not necessarily the IMAGE or
                IMAGES that you want (this is why we are doing this!)
    filename  - this is created automatically by a function that parses the
                url. It does NOT matter if the post is for a multi-image
                gallery because you will be making a new Download object for
                each image in that gallery anyway
    md5       - you set this once you have downloaded the image it's one of
                the last things you do but you still check it against the
                database to avoid duplicate images

The approach that I take for writing plugins is typically to have the execute
function call a helper function that returns an img_url,
typically I just run a little xpath, nothing too fancy.

This important part is to create the self.current objectand set it to a
Download object with a valid url so that the BasePlugin can do its work.

For example,for non direct imgur links, it looks like this (abridged):

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

If you have a gallery, it gets slightly more complicated. You cannot simply
set the self.current object because you will only get the last object that
you set it to.

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