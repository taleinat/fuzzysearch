===============================
fuzzysearch
===============================

.. image:: https://img.shields.io/pypi/v/fuzzysearch.svg?style=flat
    :target: https://pypi.python.org/pypi/fuzzysearch
    :alt: Latest Version

.. image:: https://img.shields.io/travis/taleinat/fuzzysearch.svg?branch=master
    :target: https://travis-ci.org/taleinat/fuzzysearch/branches
    :alt: Build & Tests Status

.. image:: https://img.shields.io/coveralls/taleinat/fuzzysearch.svg?branch=master
    :target: https://coveralls.io/r/taleinat/fuzzysearch?branch=master
    :alt: Test Coverage

.. image:: https://img.shields.io/pypi/dm/fuzzysearch.svg?style=flat
    :target: https://pypi.python.org/pypi/fuzzysearch
    :alt: Downloads

.. image:: https://img.shields.io/pypi/wheel/fuzzysearch.svg?style=flat
    :target: https://pypi.python.org/pypi/fuzzysearch
    :alt: Wheels

.. image:: https://img.shields.io/pypi/pyversions/fuzzysearch.svg?style=flat
    :target: https://pypi.python.org/pypi/fuzzysearch
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/implementation/fuzzysearch.svg?style=flat
    :target: https://pypi.python.org/pypi/fuzzysearch
    :alt: Supported Python implementations

.. image:: https://img.shields.io/pypi/l/fuzzysearch.svg?style=flat
    :target: https://pypi.python.org/pypi/fuzzysearch/
    :alt: License

fuzzysearch is a Python library for fuzzy substring searches. It implements efficient
ad-hoc searching for approximate sub-sequences. Matching is done using a generalized
Levenshtein Distance metric, with configurable parameters.

* Free software: `MIT license <LICENSE>`_
* Documentation: http://fuzzysearch.rtfd.org.

Installation
------------
Just install using pip::

    $ pip install fuzzysearch

Features
--------

* Fuzzy sub-sequence search: Find parts of a sequence which match a given
  sub-sequence.
* Easy to use: A single function to call which returns a list of matches.
* Set a maximum Levenshtein Distance for matches, including individual limits
  for the number of substitutions, insertions and/or deletions allowed for
  near-matches.
* Includes optimized implementations for specific use-cases, e.g. allowing
  only substitutions.

Simple Examples
---------------
Just call `find_near_matches()` with the sequence to search, the sub-sequence
you're looking for, and the matching parameters:

.. code:: python

    >>> from fuzzysearch import find_near_matches
    # search for 'PATTERN' with a maximum Levenshtein Distance of 1
    >>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1)
    [Match(start=3, end=9, dist=1)]

.. code:: python

    >>> sequence = '''\
    GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGTCACACACACA
    TTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACACATTAGACGCGTACATAGACA
    CAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATACTCGCGTAGTCGTGGGAGGCAAGGCACACAG
    GGGATAGG'''
    >>> subsequence = 'TGCACTGTAGGGATAACAAT' # distance = 1
    >>> find_near_matches(subsequence, sequence, max_l_dist=2)
    [Match(start=3, end=24, dist=1)]

Advanced Example
----------------
If needed (for optimization) you can choose a specific search implementation:

.. code:: python

    >>> from fuzzysearch import find_near_matches_with_ngrams
    >>> find_near_matches_with_ngrams(subsequence, sequence, max_l_dist=2)
    [Match(start=3, end=24, dist=1)]
