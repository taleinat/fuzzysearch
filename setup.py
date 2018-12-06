#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement

import os
import sys

from setuptools import setup, Extension
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, \
     DistutilsPlatformError

# --noexts: don't try building the C extensions
if '--noexts' in sys.argv[1:]:
    del sys.argv[sys.argv[1:].index('--noexts') + 1]
    noexts = True
else:
    noexts = False


def readfile(file_path):
    dir_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dir_path, file_path), 'r') as f:
        return f.read()

readme = readfile('README.rst')
history = readfile('HISTORY.rst').replace('.. :changelog:', '')


# Fail safe compilation based on markupsafe's, which in turn was shamelessly
# stolen from the simplejson setup.py file.  Original author: Bob Ippolito

is_jython = 'java' in sys.platform
is_pypy = hasattr(sys, 'pypy_version_info')

ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)
if sys.platform == 'win32' and sys.version_info > (2, 6):
    # 2.6's distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    # It can also raise ValueError http://bugs.python.org/issue7511
    ext_errors += (IOError, ValueError)


class BuildFailed(Exception):
    pass


class ve_build_ext(build_ext):
    """This class allows C extension building to fail."""

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()
        except ValueError:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(sys.exc_info()[1]): # works with Python 2 and 3
                raise BuildFailed()
            raise


_substitutions_only_module = Extension(
    'fuzzysearch._substitutions_only',
    sources=['src/fuzzysearch/_substitutions_only.c',
             'src/fuzzysearch/memmem.c'],
    include_dirs=['.'],
)
_common_module = Extension(
    'fuzzysearch._common',
    sources=['src/fuzzysearch/_common.c',
             'src/fuzzysearch/memmem.c'],
    include_dirs=['.'],
)
_generic_search_module = Extension(
    'fuzzysearch._generic_search',
    sources=['src/fuzzysearch/_generic_search.c',
             'src/fuzzysearch/memmem.c'],
    include_dirs=['.'],
)
_levenshtein_ngrams_module = Extension(
    'fuzzysearch._levenshtein_ngrams',
    sources=['src/fuzzysearch/_levenshtein_ngrams.c'],
    include_dirs=['.'],
)
# pymemmem_module = Extension(
#     'fuzzysearch._pymemmem',
#     sources=['src/fuzzysearch/_pymemmem.c',
#              'src/fuzzysearch/memmem.c',
#              'src/fuzzysearch/wordlen_memmem.c'],
#     include_dirs=['.'],
# )


def run_setup(with_binary=True):
    ext_modules = [
        _substitutions_only_module,
        _common_module,
        _generic_search_module,
        _levenshtein_ngrams_module,
        # pymemmem_module,
    ]
    if not with_binary:
        ext_modules = []

    setup(
        name='fuzzysearch',
        version='0.6.0',
        description='fuzzysearch is useful for finding approximate subsequence matches',
        long_description=readme + '\n\n' + history,
        author='Tal Einat',
        author_email='taleinat@gmail.com',
        url='https://github.com/taleinat/fuzzysearch',
        packages=['fuzzysearch'],
        package_dir={'': 'src'},
        ext_modules=ext_modules,
        install_requires=[
            'six',
        ],
        license='MIT',
        keywords='fuzzysearch',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: MacOS :: MacOS X',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: Implementation :: CPython',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        cmdclass={'build_ext': ve_build_ext},
    )


def try_building_extension():
    try:
        run_setup(True)
    except BuildFailed:
        line = '=' * 74
        build_ext_warning = 'WARNING: The C extensions could not be ' \
                            'compiled; speedups are not enabled.'

        print(line)
        print(build_ext_warning)
        print('Failure information, if any, is above.')
        print('Retrying the build without the C extension now.')
        print('')

        run_setup(False)

        print(line)
        print(build_ext_warning)
        print('Plain-Python installation succeeded.')
        print(line)

if not (noexts or is_pypy or is_jython):
    try_building_extension()
else:
    run_setup(False)
