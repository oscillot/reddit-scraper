Each plugin must have an `execute` function that accepts the list of child
dictionaries as he first positional argument and the lit of candidate
dictionaries where each 'url' key is a valid direct link to an image. If any
http requests are made, HTTPErrors should be caught and reported to a print on
 the console (for now) and should not halt execution of the tool.

The execute function may call other functions as needed.

See the included:
* direct_links.py
* imgur_albums.py
* deviant_art.py

For examples.