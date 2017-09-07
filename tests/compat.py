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
# It is also used here in versions 2.7, 3.2 and 3.3 to make features added
# in version 3.4 available (specifically, TestCase.subTest).
if sys.version_info < (3, 4):
    import unittest2 as unittest
else:
    import unittest

# The `mock` module was added to the stdlib as `unittest.mock` in Python
# version 3.3.
if sys.version_info < (3, 3):
    import mock
else:
    import unittest.mock as mock
