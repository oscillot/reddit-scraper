import os
import sys
from base_plugin import *

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

for plugin in plugin_list:
    try:
        loaded = __import__(plugin)
        for attr in dir(loaded):
            try:
                cls = getattr(loaded, attr)
                if issubclass(cls, BasePlugin) and cls.__name__ != 'BasePlugin':
                    good_plugins.append(cls.__name__)
                    loaded_plugins.append(cls)
            except TypeError:
                pass
    except ImportError, e:
        print '%s failed to load: %s\n' % (cls.__name__, e)
        failed_plugins.append(cls)

sys.path.remove(plugins_folder)

print 'Loaded the following plugins successfully: %s\n' % ', '.join(good_plugins)