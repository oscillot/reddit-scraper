Each plugin must have an `execute` function that accepts a single member of
the list of child dictionaries as he first positional argument and the list
of candidate dictionaries where each 'url' key is a valid direct link to an
image. Try to catch any errors yourself in the plugin.

Plugins must inherit from the BasePlugin class (this is checked on plugin
import) The constructor of the BasePlugin class sets the list of candidates
passed to the plugin as a class attribute. It also sets empty list class
attributes for links to_acquire, links handled and exceptions. The to_acquire
 and handled lists are lists of dictionaries in the same format as the
 candidates list (dictionaries as returned from the reddit json api).

Finally, the constructor will call the __execute function which wraps the
overriddable execute method in a generic exception handler that will catch
any exception not explicitly caught y the plugin to keep plugins from
stopping the job. Exceptions are logged as a 3-tuple in the with the plugin,
data and exception and are displayed in the console at the end of the run.

The execute function may call other functions as needed,
and should in most cases for the sake of readability and maintainability.

See the included plugins for examples. Direct link is probably not a good
example to look at as it is the only plugin that has only and execute method
and nothing else.

This is my first attempt at a plugin system that doesn't require you to
explicitly register plugins. Do you have an opinion on this? Good or bad,
it is welcome! Please get in touch!