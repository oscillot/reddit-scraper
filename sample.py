import os
from reddit_connect import RedditConnect
from image_getter import ImageGetter

#run this manually, through jenkins or as a cron job

#pass in your username and pw. All connections are ssl, see reddit_connect.py
rc = RedditConnect('username', 'password')
#perform the login
rc.login()
#retrieve X pages of likes
liked_data = rc.get_liked(max_pages=5)
#if you use jenkins with envinject, you can specify a multi-reddit or list
# there, otherwise pass a list in directly
# e.g.
# my_subs = \
# os.environ.get('MY_SUBS').lstrip('http://www.reddit.com/r/').split('+')
my_subs = ['apocalypseporn', 'bigwallpapers', 'conceptart',
           'creepywallpaper', 'creepywallpapers', 'cyberpunk', 'FUI',
           'FuturePorn', 'glitchart', 'grim', 'imaginarylandscapes',
           'imaginarytechnology', 'multiscreen', 'originalbackgrounds',
           'postapocalyptic', 'sciencefiction', 'scifi', 'specart',
           'steampunk']
#get the list of candidate images
candidates = rc.get_upvoted_wallpapers(my_subs, liked_data)
#instaniate the image acquisition class with a daabase name,
# list of candidates and set a location to save images to.
ig = ImageGetter(database='db_name', candidates=candidates,
                 output=os.path.join('X:\\', 'location_to_save_to'))
ig.acquire()

#If you use Jenkins with the EnvInject plugin, you can expose parameter input to the web interface and configure from
# over your network instead of editing the module directly, e.g.:

#liked_data = rc.get_liked(max_pages=int(os.environ.get('MAX_PAGES')))

#if you are like me and have a multi-reddit you use to get images from and update frequetly, you can pass in the url
# directly using something like this:

#my_subs = os.environ.get('PAUL_SUBS').lstrip('http://www.reddit.com/r/').split('+')
