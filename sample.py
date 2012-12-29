import os
from scraper import RedditConnect

#pass in your username and pw. All connections are ssl, see scraper.py
rc = RedditConnect('username', 'password', 'db_name')
#perform the login
rc.login()
#retrieve X pages of likes
liked_data = rc.get_liked(max_pages=5)
#if you use jenkins with envinject, you can specify a multi-reddit or list there, otherwise pass a list in directly
# and call on a schedule as a cron job
my_subs = ['apocalypseporn','bigwallpapers','conceptart','creepywallpaper','creepywallpapers','cyberpunk','FUI',
           'FuturePorn','glitchart','grim','imaginarylandscapes','imaginarytechnology','multiscreen',
           'originalbackgrounds','postapocalyptic','sciencefiction','scifi','specart','steampunk']
#get the list of candidate images
candidates = rc.get_upvoted_wallpapers(my_subs, liked_data)
#set a location to save to.
rc.acquire(candidates, os.path.join('X:\\', 'location_to_save_to'))

#If you use Jenkins with the EnvInject plugin, you can expose parameter input to the web interface and configure from
# over your network instead of editing the module directly, e.g.:

#liked_data = rc.get_liked(max_pages=int(os.environ.get('MAX_PAGES')))

#if you are like me and have a multi-reddit you use to get images from and update frequetly, you can pass in the url
# directly using something like this:

#my_subs = os.environ.get('PAUL_SUBS').lstrip('http://www.reddit.com/r/').split('+')
