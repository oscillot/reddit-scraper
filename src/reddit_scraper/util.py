import re
import unicodedata
from StringIO import StringIO
from PIL import Image

def ensure_ascii(text):
    return unicodedata.normalize('NFD', unicode(text)).encode('ascii',
                                                       'xmlcharrefreplace')


def extract_domain(url):
    dom_pat = re.compile(r'^.*://(?:[wW]{3}\.)?([^:/]*).*$')
    domain = re.findall(dom_pat, url)[0]
    #truncate username subdomains like for e.g. deviant art and useless ones
    # like www
    if domain.count('.') > 1:
        #but don't be overzealous and do this on sites that end in like .co.uk
        if len(domain.split('.')[-2]) > 2:
            domain = '.'.join(domain.split('.')[-2:])
        else:
            if domain.count('.') > 2 and len(domain.split('.')[-2]) > 2:
                #alternate ruleset for e.g. .co.uk
                domain = '.'.join(domain.split('.')[1:])
    return domain


def substract(string):
    substractor = re.compile(r'^/r/(.*)/$')
    match = substractor.search(string)
    if match:
        return match.group(1)
    else:
        return string


def gif_is_animated(data):
    im = Image.open(StringIO(data))
    try:
        im.seek(1)
    except EOFError:
        im.close()
        return False
    else:
        im.close()
        return True
