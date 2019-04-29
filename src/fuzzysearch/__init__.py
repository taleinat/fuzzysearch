"""A library for finding approximate subsequence matches.

Contains several implementations of fuzzy sub-sequence search functions. Such
functions find parts of a sequence which match a given sub-sequence up to a
given maximum Levenshtein distance.

The simplest use is via the find_near_matches utility function, which chooses
a suitable fuzzy search implementation based on the given parameters.

Example:
>>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1)
[Match(start=3, end=9, dist=1)]
"""
__author__ = 'Tal Einat'
__email__ = 'taleinat@gmail.com'
__version__ = '0.6.2'

__all__ = [
    'find_near_matches',
    'Match',
]


from fuzzysearch.common import Match, LevenshteinSearchParams
from fuzzysearch.generic_search import GenericSearch
from fuzzysearch.levenshtein import LevenshteinSearch
from fuzzysearch.search_exact import ExactSearch
from fuzzysearch.substitutions_only import SubstitutionsOnlySearch


def find_near_matches(subsequence, sequence,
                      max_substitutions=None,
                      max_insertions=None,
                      max_deletions=None,
                      max_l_dist=None):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the maximum allowed number of character substitutions
    * the maximum allowed number of new characters inserted
    * and the maximum allowed number of character deletions
    * the total number of substitutions, insertions and deletions
      (a.k.a. the Levenshtein distance)
    """
    search_params = LevenshteinSearchParams(max_substitutions,
                                            max_insertions,
                                            max_deletions,
                                            max_l_dist)
    search_class = choose_search_class(search_params)
    matches = search_class.search(subsequence, sequence, search_params)
    return search_class.consolidate_matches(matches)


def choose_search_class(search_params):
    max_substitutions, max_insertions, max_deletions, max_l_dist = search_params.unpacked

    # if the limitations are so strict that only exact matches are allowed,
    # use search_exact()
    if max_l_dist == 0:
        return ExactSearch

    # if only substitutions are allowed, use find_near_matches_substitutions()
    elif max_insertions == 0 and max_deletions == 0:
        return SubstitutionsOnlySearch

    # if it is enough to just take into account the maximum Levenshtein
    # distance, use find_near_matches_levenshtein()
    elif max_l_dist <= min(
        (max_substitutions if max_substitutions is not None else (1 << 29)),
        (max_insertions if max_insertions is not None else (1 << 29)),
        (max_deletions if max_deletions is not None else (1 << 29)),
    ):
        return LevenshteinSearch

    # if none of the special cases above are met, use the most generic version
    else:
        return GenericSearch
