import re
import unicodedata

__author__ = 'Oscillot'


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