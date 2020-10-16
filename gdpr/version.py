from itertools import imap
VERSION = (0, 2, 12)


def get_version():
    return u'.'.join(imap(unicode, VERSION))
