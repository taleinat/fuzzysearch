"""A library for finding approximate subsequence matches.

Contains several implementations of fuzzy sub-sequence search functions. Such
functions find parts of a sequence which match a given sub-sequence up to a
given maximum Levenshtein distance.

The simplest use is via the find_near_matches utility function, which chooses
a suitable fuzzy search implementation based on the given parameters.

Example:
>>> find_near_matches('PATTERN', 'aaaPATERNaaa', max_l_dist=1)
[Match(start=3, end=9, dist=1)]
"""
__author__ = 'Tal Einat'
__email__ = 'taleinat@gmail.com'
__version__ = '0.3.0'

__all__ = [
    'find_near_matches',
    'Match',
]


from fuzzysearch.common import Match, get_best_match_in_group, group_matches, \
    search_exact
from fuzzysearch.levenshtein import find_near_matches_levenshtein
from fuzzysearch.substitutions_only import find_near_matches_substitutions
from fuzzysearch.generic_search import find_near_matches_generic, \
    find_near_matches_generic_linear_programming, _check_arguments, \
    _get_max_l_dist


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
    _check_arguments(subsequence, sequence, max_substitutions, max_insertions,
                     max_deletions, max_l_dist)

    max_l_dist = _get_max_l_dist(max_substitutions, max_insertions,
                                 max_deletions, max_l_dist)

    # if the limitations are so strict that only exact matches are allowed,
    # use search_exact()
    if max_l_dist == 0:
        return [
            Match(start_index, start_index + len(subsequence), 0)
            for start_index in search_exact(subsequence, sequence)
        ]

    # if only substitutions are allowed, use find_near_matches_substitutions()
    elif max_insertions == 0 and max_deletions == 0:
        max_subs = \
            min([x for x in [max_l_dist, max_substitutions] if x is not None])
        return find_near_matches_substitutions(subsequence, sequence, max_subs)

    # if it is enough to just take into account the maximum Levenshtein
    # distance, use find_near_matches_levenshtein()
    elif max_l_dist <= min(
        (max_substitutions if max_substitutions is not None else (1 << 29)),
        (max_insertions if max_insertions is not None else (1 << 29)),
        (max_deletions if max_deletions is not None else (1 << 29)),
    ):
        return find_near_matches_levenshtein(subsequence, sequence, max_l_dist)

    # if none of the special cases above are met, use the most generic version
    else:
        return find_near_matches_generic(subsequence, sequence,
                                         max_substitutions, max_insertions,
                                         max_deletions, max_l_dist)
