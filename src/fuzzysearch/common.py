import sys
from collections import namedtuple
from functools import wraps
from six.moves import range, zip

__all__ = [
    'Match', 'Ngram',
    'search_exact', 'count_differences_with_maximum',
    'group_matches', 'get_best_match_in_group',
]


CLASSES_WITH_INDEX = (list, tuple)
if sys.version_info >= (3,):
    CLASSES_WITH_FIND = (bytes, str)
else:
    CLASSES_WITH_FIND = (str, unicode)

try:
    from Bio.Seq import Seq
except ImportError:
    pass
else:
    CLASSES_WITH_FIND += (Seq,)


Match = namedtuple('Match', ['start', 'end', 'dist'])
Ngram = namedtuple('Ngram', ['start', 'end'])


class LevenshteinSearchParams(object):
    def __init__(self,
                 max_substitutions=None,
                 max_insertions=None,
                 max_deletions=None,
                 max_l_dist=None):
        self.check_params_valid(max_substitutions, max_insertions,
                                max_deletions, max_l_dist)

        self.max_substitutions = max_substitutions
        self.max_insertions = max_insertions
        self.max_deletions = max_deletions
        self.max_l_dist = self._get_max_l_dist(
            max_substitutions, max_insertions,
            max_deletions, max_l_dist,
        )

    @property
    def unpacked(self):
        return self.max_substitutions, self.max_insertions, self.max_deletions, self.max_l_dist

    @classmethod
    def check_params_valid(cls,
                     max_substitutions, max_insertions,
                     max_deletions, max_l_dist):
        if not all(x is None or isinstance(x, int)
                   for x in
                   [max_substitutions, max_insertions, max_deletions, max_l_dist]):
            raise TypeError("All limits must be integers or None")

        if max_l_dist is None:
            n_limits = (
                (1 if max_substitutions is not None else 0) +
                (1 if max_insertions is not None else 0) +
                (1 if max_deletions is not None else 0)
            )
            if n_limits < 3:
                if n_limits == 0:
                    raise ValueError('No limitations given!')
                elif max_substitutions is None:
                    raise ValueError('# substitutions must be limited!')
                elif max_insertions is None:
                    raise ValueError('# insertions must be limited!')
                elif max_deletions is None:
                    raise ValueError('# deletions must be limited!')

    @classmethod
    def _get_max_l_dist(cls,
                        max_substitutions, max_insertions,
                        max_deletions, max_l_dist):
        bignum = 1 << 29
        maxes_sum = (
            (max_substitutions if max_substitutions is not None else bignum) +
            (max_insertions if max_insertions is not None else bignum) +
            (max_deletions if max_deletions is not None else bignum)
        )
        return (
            max_l_dist
            if max_l_dist is not None and max_l_dist <= maxes_sum
            else maxes_sum
        )


def search_exact(subsequence, sequence, start_index=0, end_index=None):
    if not subsequence:
        raise ValueError('subsequence must not be empty')

    if end_index is None:
        end_index = len(sequence)

    if isinstance(sequence, CLASSES_WITH_FIND):
        def find_in_index_range(start_index):
            return sequence.find(subsequence, start_index, end_index)
    elif isinstance(sequence, CLASSES_WITH_INDEX):
        first_item = subsequence[0]
        first_item_last_index = end_index - (len(subsequence) - 1)
        def find_in_index_range(start_index):
            while True:
                try:
                    first_index = sequence.index(first_item, start_index, first_item_last_index)
                    start_index = first_index + 1
                except ValueError:
                    return -1
                for subseq_index in range(1, len(subsequence)):
                    if sequence[first_index + subseq_index] != subsequence[subseq_index]:
                        break
                else:
                    return first_index
    else:
        raise TypeError('unsupported sequence type: %s' % type(sequence))

    index = find_in_index_range(start_index)
    while index >= 0:
        yield index
        index = find_in_index_range(index + 1)


def count_differences_with_maximum(sequence1, sequence2, max_differences):
    n_different = 0
    for item1, item2 in zip(sequence1, sequence2):
        if item1 != item2:
            n_different += 1
            if n_different == max_differences:
                return n_different
    return n_different

try:
    from fuzzysearch._common import count_differences_with_maximum_byteslike, \
        search_exact_byteslike
except ImportError:
    pass
else:
    _count_differences_with_maximum = count_differences_with_maximum
    @wraps(_count_differences_with_maximum)
    def count_differences_with_maximum(sequence1, sequence2, max_differences):
        try:
            return count_differences_with_maximum_byteslike(sequence1,
                                                            sequence2,
                                                            max_differences)
        except TypeError:
            return _count_differences_with_maximum(sequence1, sequence2,
                                                   max_differences)

    _search_exact = search_exact
    @wraps(_search_exact)
    def search_exact(subsequence, sequence, start_index=0, end_index=None):
        try:
            return search_exact_byteslike(subsequence, sequence,
                                          start_index, end_index if end_index is not None else -1)
        except (TypeError, UnicodeEncodeError):
            return _search_exact(subsequence, sequence, start_index, end_index)


class GroupOfMatches(object):
    def __init__(self, match):
        assert match.start < match.end
        self.start = match.start
        self.end = match.end
        self.matches = set([match])

    def is_match_in_group(self, match):
        return not (match.end <= self.start or match.start >= self.end)

    def add_match(self, match):
        self.matches.add(match)
        self.start = min(self.start, match.start)
        self.end = max(self.end, match.end)


def group_matches(matches):
    groups = []
    for match in matches:
        overlapping_groups = [g for g in groups if g.is_match_in_group(match)]
        if not overlapping_groups:
            groups.append(GroupOfMatches(match))
        elif len(overlapping_groups) == 1:
            overlapping_groups[0].add_match(match)
        else:
            new_group = GroupOfMatches(match)
            for group in overlapping_groups:
                for match in group.matches:
                    new_group.add_match(match)
            groups = [g for g in groups if g not in overlapping_groups]
            groups.append(new_group)

    return [group.matches for group in groups]


def get_best_match_in_group(group):
    # return longest match amongst those with the shortest distance
    return min(group, key=lambda match: (match.dist, -(match.end - match.start)))
