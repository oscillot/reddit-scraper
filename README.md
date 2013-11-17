The reddit-scraper requires lxml. Please install it from lxml.de.
For windows, I used the prebuilt binaries at:
http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

This project was built using lxml 3.02, and Python 2.7.3,
though other versions may work. It also requires sqlalchemy and the Python
Image Library.

Please run setup.py to try and get these dependencies. The "fork" of PIL
expected here is 'pillow'.

#TODO make this able to be run from any location

currently on windows it is necessary to run this from the root of C:\
currently on *nix it is necessary to run this from the root of the user's
home folder