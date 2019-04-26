import sys


__all__ = [
    'izip',
    'text_type',
    'xrange',
]


if sys.version_info < (3,):
    int_types = (int, long)
    from itertools import izip
    text_type = unicode
    xrange = xrange
else:
    int_types = (int,)
    izip = zip
    text_type = str
    xrange = range
