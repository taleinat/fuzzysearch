#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from distutils.core import setup, Extension


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

_substitutions_only_module = Extension(
    'fuzzysearch._substitutions_only',
    sources=['fuzzysearch/_substitutions_only.c', 'fuzzysearch/memmem.c'],
    include_dirs=['.'],
)
_common_module = Extension(
    'fuzzysearch._common',
    sources=['fuzzysearch/_common.c', 'fuzzysearch/memmem.c'],
    include_dirs=['.'],
)
_generic_search_module = Extension(
    'fuzzysearch._generic_search',
    sources=['fuzzysearch/_generic_search.c', 'fuzzysearch/memmem.c'],
    include_dirs=['.'],
)
pymemmem_module = Extension(
    'fuzzysearch._pymemmem',
    sources=['fuzzysearch/_pymemmem.c', 'fuzzysearch/memmem.c', 'fuzzysearch/kmp.c', 'fuzzysearch/wordlen_memmem.c'],
    include_dirs=['.'],
)

setup(
    name='fuzzysearch',
    version='0.2.2',
    description='fuzzysearch is useful for finding approximate subsequence matches',
    long_description=readme + '\n\n' + history,
    author='Tal Einat',
    author_email='taleinat@gmail.com',
    url='https://github.com/taleinat/fuzzysearch',
    packages=[
        'fuzzysearch',
    ],
    package_dir={'fuzzysearch': 'fuzzysearch'},
    ext_modules=[_substitutions_only_module, _common_module,
                 _generic_search_module, pymemmem_module],
    license="MIT",
    keywords='fuzzysearch',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
)
