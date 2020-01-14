===========
fuzzysearch
===========

.. image:: https://img.shields.io/pypi/v/fuzzysearch.svg?style=flat
    :target: https://pypi.python.org/pypi/fuzzysearch
    :alt: Latest Version

.. image:: https://img.shields.io/travis/taleinat/fuzzysearch.svg?branch=master
    :target: https://travis-ci.org/taleinat/fuzzysearch/branches
    :alt: Build & Tests Status

.. image:: https://img.shields.io/coveralls/taleinat/fuzzysearch.svg?branch=master
    :target: https://coveralls.io/r/taleinat/fuzzysearch?branch=master
    :alt: Test Coverage

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

**Easy Python fuzzy search that just works, fast!**

.. code:: python

    >>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1)
    [Match(start=3, end=9, dist=1, matched="PATERN")]

* Approximate sub-string searches

* Two simple functions to use: one for in-memory data and one for files

  * Fastest search algorithm is chosen automatically

* Levenshtein Distance metric with configurable parameters

  * Separately configure the max. allowed distance, substitutions, deletions
    and insertions

* Advanced algorithms with optional C and Cython optimizations

* Properly handles Unicode; special optimizations for binary data

* Extensively tested

* Free software: `MIT license <LICENSE>`_

For more info, see the `documentation <http://fuzzysearch.rtfd.org>`_.


Installation
------------

.. code::

    $ pip install fuzzysearch

This will work even if installing the C and Cython extensions fails, using
pure-Python fallbacks.


Usage
-----
Just call ``find_near_matches()`` with the sub-sequence you're looking for,
the sequence to search, and the matching parameters:

.. code:: python

    >>> from fuzzysearch import find_near_matches
    # search for 'PATTERN' with a maximum Levenshtein Distance of 1
    >>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1)
    [Match(start=3, end=9, dist=1, matched="PATERN")]

To search in a file, use ``find_near_matches_in_file()`` similarly:

.. code:: python

    >>> from fuzzysearch import find_near_matches_in_file
    >>> with open('data_file', 'rb') as f:
    ...     find_near_matches_in_file(b'PATTERN', f, max_l_dist=1)
    [Match(start=3, end=9, dist=1, matched="PATERN")]


Examples
--------

*fuzzysearch* is great for ad-hoc searches of genetic data, such as DNA or
protein sequences, before reaching for "heavier", domain-specific tools like
BioPython:

.. code:: python

    >>> sequence = '''\
    GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGTCACACACACA
    TTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACACATTAGACGCGTACATAGACA
    CAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATACTCGCGTAGTCGTGGGAGGCAAGGCACACAG
    GGGATAGG'''
    >>> subsequence = 'TGCACTGTAGGGATAACAAT' # distance = 1
    >>> find_near_matches(subsequence, sequence, max_l_dist=2)
    [Match(start=3, end=24, dist=1, matched="TAGCACTGTAGGGATAACAAT")]

BioPython sequences are also supported:

.. code:: python

    >>> from Bio.Seq import Seq
    >>> from Bio.Alphabet import IUPAC
    >>> sequence = Seq('''\
    GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGTCACACACACA
    TTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACACATTAGACGCGTACATAGACA
    CAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATACTCGCGTAGTCGTGGGAGGCAAGGCACACAG
    GGGATAGG''', IUPAC.unambiguous_dna)
    >>> subsequence = Seq('TGCACTGTAGGGATAACAAT', IUPAC.unambiguous_dna)
    >>> find_near_matches(subsequence, sequence, max_l_dist=2)
    [Match(start=3, end=24, dist=1, matched="TAGCACTGTAGGGATAACAAT")]


Matching Criteria
-----------------
The search function supports four possible match criteria, which may be
supplied in any combination:

* maximum Levenshtein distance (``max_l_dist``)

* maximum # of subsitutions

* maximum # of deletions ("delete" = skip a character in the sub-sequence)

* maximum # of insertions ("insert" = skip a character in the sequence)

Not supplying a criterion means that there is no limit for it. For this reason,
one must always supply ``max_l_dist`` and/or all other criteria.

.. code:: python

    >>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1)
    [Match(start=3, end=9, dist=1, matched="PATERN")]

    # this will not match since max-deletions is set to zero
    >>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1, max_deletions=0)
    []

    # note that a deletion + insertion may be combined to match a substution
    >>> find_near_matches('PATTERN', '---PAT-ERN---', max_deletions=1, max_insertions=1, max_substitutions=0)
    [Match(start=3, end=10, dist=1, matched="PAT-ERN")] # the Levenshtein distance is still 1

    # ... but deletion + insertion may also match other, non-substitution differences
    >>> find_near_matches('PATTERN', '---PATERRN---', max_deletions=1, max_insertions=1, max_substitutions=0)
    [Match(start=3, end=10, dist=2, matched="PATERRN")]


When to Use Other Tools
-----------------------

* Use case: Search through a list of strings for almost-exactly matching
  strings. For example, searching through a list of names for possible slight
  variations of a certain name.

  Suggestion: Consider using `fuzzywuzzy <https://github.com/seatgeek/fuzzywuzzy>`_.
