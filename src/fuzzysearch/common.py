from functools import wraps

from fuzzysearch.compat import int_types, text_type, xrange

from attr import attrs, attrib


__all__ = [
    'Match', 'LevenshteinSearchParams',
    'search_exact', 'count_differences_with_maximum',
    'group_matches', 'get_best_match_in_group',
]


CLASSES_WITH_INDEX = (list, tuple)
CLASSES_WITH_FIND = (bytes, text_type)

try:
    from Bio.Seq import Seq
except ImportError:
    pass
else:
    CLASSES_WITH_FIND += (Seq,)


@attrs(frozen=True, slots=True)
class Match(object):
    start = attrib(type=int)
    end = attrib(type=int)
    dist = attrib(type=int)

    if __debug__:
        def __attrs_post_init__(self):
            if not (isinstance(self.start, int_types) and self.start >= 0):
                raise ValueError('start must be a non-negative integer')
            if not (isinstance(self.end, int_types) and self.end >= self.start):
                raise ValueError('end must be an integer no smaller than start')
            if not (isinstance(self.dist, int_types) and self.dist >= 0):
                print(self.dist)
                raise ValueError('dist must be a non-negative integer')


@attrs(frozen=True, slots=True)
class LevenshteinSearchParams(object):
    max_substitutions = attrib(default=None)
    max_insertions = attrib(default=None)
    max_deletions = attrib(default=None)
    max_l_dist = attrib(default=None)

    def __attrs_post_init__(self):
        self._check_params_valid()
        object.__setattr__(self, 'max_l_dist', self._normalize_max_l_dist())

    @property
    def unpacked(self):
        return self.max_substitutions, self.max_insertions, self.max_deletions, self.max_l_dist

    def _check_params_valid(self):
        if not all(x is None or (isinstance(x, int) and x >= 0)
                   for x in [
                       self.max_substitutions,
                       self.max_insertions,
                       self.max_deletions,
                       self.max_l_dist
                   ]):
            raise TypeError("All limits must be positive integers or None.")

        if self.max_l_dist is None:
            n_limits = (
                (1 if self.max_substitutions is not None else 0) +
                (1 if self.max_insertions is not None else 0) +
                (1 if self.max_deletions is not None else 0)
            )
            if n_limits < 3:
                if n_limits == 0:
                    raise ValueError('No limitations given!')
                elif self.max_substitutions is None:
                    raise ValueError('# substitutions must be limited!')
                elif self.max_insertions is None:
                    raise ValueError('# insertions must be limited!')
                elif self.max_deletions is None:
                    raise ValueError('# deletions must be limited!')

    def _normalize_max_l_dist(self):
        maxes_sum = sum(
            x if x is not None else 1 << 29
            for x in [
                self.max_substitutions,
                self.max_insertions,
                self.max_deletions,
            ]
        )
        return (
            self.max_l_dist
            if self.max_l_dist is not None and self.max_l_dist <= maxes_sum
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
                for subseq_index in xrange(1, len(subsequence)):
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
        if end_index is None:
            end_index = len(sequence)

        try:
            return search_exact_byteslike(subsequence, sequence,
                                          start_index, end_index)
        except (TypeError, UnicodeEncodeError):
            return _search_exact(subsequence, sequence, start_index, end_index)


class GroupOfMatches(object):
    def __init__(self, match):
        assert match.start <= match.end
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
