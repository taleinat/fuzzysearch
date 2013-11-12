#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='fuzzysearch',
    version='0.1.0',
    description='fuzzysearch is useful for finding approximate subsequence matches',
    long_description=readme + '\n\n' + history,
    author='Tal Einat',
    author_email='taleinat@gmail.com',
    url='https://github.com/taleinat/fuzzysearch',
    packages=[
        'fuzzysearch',
    ],
    package_dir={'fuzzysearch': 'fuzzysearch'},
    include_package_data=True,
    install_requires=[
    ],
    use_2to3=True,
    license="MIT",
    zip_safe=False,
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
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='tests',
)