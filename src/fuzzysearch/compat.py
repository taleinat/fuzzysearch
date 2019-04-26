import sys


__all__ = [
    'izip',
    'text_type',
    'xrange',
]


if sys.version_info < (3,):
    from itertools import izip
    text_type = unicode
    xrange = xrange
else:
    izip = zip
    text_type = str
    xrange = range
