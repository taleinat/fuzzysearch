import sys


__all__ = [
    'int_types',
    'izip',
    'text_type',
    'xrange',
]


if sys.version_info < (3,):
    PY2 = True
    PY3 = False
    int_types = (int, long)
    from itertools import izip
    text_type = unicode
    xrange = xrange
else:
    PY2 = False
    PY3 = True
    int_types = (int,)
    izip = zip
    text_type = str
    xrange = range
