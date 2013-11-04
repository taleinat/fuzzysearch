"""Compatibility support of testing tools for different Python versions"""
# The required modules are installed as necessary for different Python
# versions by `tox`. See `tox.ini` for details.
import sys

__all__ = [
    'unittest',
    'mock',
]

# The `unittest2` module is a backport of the new unittest features introduced
# in Python versions 3.2 and 2.7. Use it in older versions of Python.
if sys.version_info < (2, 7) or (3, 0) <= sys.version_info < (3, 2):
    import unittest2 as unittest
else:
    import unittest

# The `mock` module was added to the stdlib as `unittest.mock` in Python
# version 3.3.
if sys.version_info < (3, 3):
    import mock
else:
    import unittest.mock as mock
