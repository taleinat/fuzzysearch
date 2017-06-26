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
The search function supports four possible match criteria, which may be supplied in any combination:
* maximum Levenshtein distance
* maximum # of subsitutions
* maximum # of deletions (elements appearing in the pattern search for, which are skipped in the matching sub-sequence)
* maximum # of insertions (elements added in the matching sub-sequence which don't appear in the pattern search for)

Not supplying a criterion means that there is no limit for it. For this reason, one must always supply `max_l_dist` and/or all of the other three criteria.

.. code:: python

    >>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1)
    [Match(start=3, end=9, dist=1)]
    
    # this will not match since max-deletions is set to zero
    >>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1, max_deletions=0)
    []
    
    # note that a deletion + insertion may be combined to match a substution
    >>> find_near_matches('PATTERN', '---PAT-ERN---', max_deletions=1, max_insertions=1, max_substitutions=0)
    [Match(start=3, end=10, dist=1)] # the Levenshtein distance is still 1

    # ... but deletion + insertion may also match other, non-substitution differences
    >>> find_near_matches('PATTERN', '---PATERRN---', max_deletions=1, max_insertions=1, max_substitutions=0)
    [Match(start=3, end=10, dist=2)]
