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
__version__ = '0.2.1'

__all__ = [
    'find_near_matches_with_ngrams',
    'find_near_matches_customized_levenshtein',
    'find_near_matches',
    'Match',
]


from fuzzysearch.common import Match, get_best_match_in_group, group_matches
from fuzzysearch.ngrams_search import find_near_matches_with_ngrams, _find_all
from fuzzysearch.custom_search import find_near_matches_customized_levenshtein


def find_near_matches(subsequence, sequence, max_l_dist):
    """Find near-matches of the subsequence in the sequence.

    This chooses a suitable fuzzy search implementation according to the given
    parameters.

    Returns a list of fuzzysearch.Match objects describing the matching parts
    of the sequence.
    """
    if not subsequence:
        raise ValueError('Given subsequence is empty!')
    if max_l_dist < 0:
        raise ValueError('Maximum Levenshtein distance must be >= 0!')

    if max_l_dist == 0:
        return [
            Match(start_index, start_index + len(subsequence), 0)
            for start_index in _find_all(subsequence, sequence)
        ]

    elif len(subsequence) // (max_l_dist + 1) >= 3:
        return find_near_matches_with_ngrams(subsequence,
                                             sequence,
                                             max_l_dist)

    else:
        matches = find_near_matches_customized_levenshtein(subsequence,
                                                           sequence,
                                                           max_l_dist)
        match_groups = group_matches(matches)
        best_matches = [get_best_match_in_group(group) for group in match_groups]
        return sorted(best_matches)
