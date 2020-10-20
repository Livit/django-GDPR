from itertools import imap
VERSION = (0, 2, 12)


def get_version():
    base = u'.'.join(imap(unicode, VERSION))
    return base + '-python2'
