import os
import sys

from reddit_scraper.plugins.base_plugin import BasePlugin


#Load an arbitrary number of arbitrarily named plugins from the plugins folder

plugin_list = []
#what the fuck is good and loaded and why are they different??
good_plugins = []
loaded_plugins = []
failed_plugins = []

plugins_folder = os.path.abspath(os.path.dirname(__file__))
for r, d, f in os.walk(plugins_folder):
    for p in f:
        if p.endswith('.py'):
            plugin_list.append(p.rstrip('.py'))

sys.path.insert(0, plugins_folder)


def valid_plugin(cls):
    #Make sure all plugins subclass the base plugin!
    if not issubclass(cls, BasePlugin):
        return False
    if cls.__name__ == 'BasePlugin':
        return False
    if not hasattr(cls, 'url_matches') and \
            type(cls.url_matches != 'instancemethod'):
        print 'Plugin Import Failed!\t %s does not have a static method ' \
              'called `url_matches` to match URLs!'
        return False
    return True

for plugin in plugin_list:
    if plugin in ['base_plugin', '__init__']:
        continue
    try:
        loaded = __import__(plugin)
        for attr in dir(loaded):
            try:
                cls = getattr(loaded, attr)
                if valid_plugin(cls):
                    good_plugins.append(cls.__name__)
                    loaded_plugins.append(cls)
            except TypeError:
                pass
    except ImportError, e:
        print '%s failed to load: %s\n' % (plugin, e)
        failed_plugins.append(plugin)

sys.path.remove(plugins_folder)

print 'Loaded the following plugins successfully: %s\n' % \
      ', '.join(good_plugins)