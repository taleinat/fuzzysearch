========
Usage
========

Simple Example
--------------
You can usually just use the `find_near_matches()` utility function, which
chooses a suitable fuzzy search implementation according to the given
parameters:

.. code:: python

    >>> from fuzzysearch.generic_search import find_near_matches_generic_ngrams
    >>> find_near_matches('PATTERN', 'aaaPATERNaaa', max_l_dist=1)
    [Match(start=3, end=9, dist=1, matched='PATERN')]

Internal Functions
------------------
If needed you can choose a specific internal search implementation. These are
not as easy to use, since they do not use the same interface as exposed by
``find_near_matches()``. There is a complete working example below.

Many of these functions require passing the fuzzy matching parameters as a
``LevenshteinSearchParams`` object, which can be created after importing the
class from ``fuzzysearch.common``.

Many of these functions also often return many overlapping search results.
These may be consolidated using the ``consolidate_overlapping_matches()``
function, also found in the ``fuzzysearch.common`` module.

Finally, some of these functions are generator functions rather than returning
a list. Wrap the call with ``list()`` if needed.

The available internal functions, by module:

* ``fuzzysearch.search_exact``
    * ``search_exact(subsequence, sequence, start_index=0, end_index=None)``
* ``fuzzysearch.generic_search``: Supports specifying any combination of fuzzy matching limitations.
    * ``find_near_matches_generic``
    * ``find_near_matches_generic_linear_programming``
    * ``find_near_matches_generic_ngrams``
    * ``has_near_match_generic_ngrams``
* ``fuzzysearch.levenshtein``: Supports only specifying the max. distance.
    * ``find_near_matches_levenshtein``
    * ``find_near_matches_levenshtein_linear_programming``
    * ``find_near_matches_levenshtein_ngrams``
* ``fuzzysearch.substitutions_only``: Allow only substitutions (fast!).
    * ``find_near_matches_substitutions()``
    * ``has_near_match_substitutions()``
    * ``find_near_matches_substitutions_lp()``
    * ``find_near_matches_substitutions_ngrams()``
    * ``has_near_match_substitutions_ngrams()``
* ``fuzzysearch.no_deletions``: Slightly faster when deletions are not allowed.
    * ``find_near_matches_no_deletions_ngrams()``

Internal Function Usage Example
+++++++++++++++++++++++++++++++

An example of using ``find_near_matches_generic_ngrams()``:

.. code:: python

    >>> sequence = '''\
    GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGTCACACACACA
    TTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACACATTAGACGCGTACATAGACA
    CAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATACTCGCGTAGTCGTGGGAGGCAAGGCACACAG
    GGGATAGG'''
    >>> subsequence = 'TGCACTGTAGGGATAACAAT' #distance 1
    >>> max_distance = 2

    >>> from fuzzysearch.generic_search import find_near_matches_generic_ngrams
    >>> from fuzzysearch import LevenshteinSearchParams
    >>> params = LevenshteinSearchParams(max_l_dist=max_distance)
    # note: this will return many overlapping results
    >>> results = find_near_matches_generic_ngrams(subsequence, sequence, params)
    >>> len(results)
    16
    # consolidate the overlapping results, keeping a "good" one from each group
    >>> from fuzzysearch.common import consolidate_overlapping_matches
    >>> consolidate_overlapping_matches(results)
    >>> [Match(start=3, end=24, dist=1, matched='TAGCACTGTAGGGATAACAAT')]
