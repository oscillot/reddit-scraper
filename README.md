The reddit-scraper requires lxml. Please install it from lxml.de.
For windows, I used the prebuilt binaries at:
http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

This project was built using lxml 3.02, and Python 2.7.3,
though other versions may work. It also requires sqlalchemy and the Python
Image Library.

Please run setup.py to try and get these dependencies. The "fork" of PIL
expeced here is 'pillow' and differs only in that you can install it with
easy_install, but as a result of the changes enabling this,
has a slightly modified import statement.

Python version prior to 2.7 do not support
automatic redirects through urllib/urllib2, so it is likely that while the
code may run, shortened URLS and pages with temporary or permanent redirects
will not be resolved properly and will remain unhandled.