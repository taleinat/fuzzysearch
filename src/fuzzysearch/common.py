from functools import wraps

from fuzzysearch.compat import int_types

from attr import attrs, attrib


__all__ = [
    'Match', 'LevenshteinSearchParams',
    'count_differences_with_maximum',
    'group_matches', 'get_best_match_in_group',
    'consolidate_overlapping_matches',
]


@attrs(frozen=True, slots=True)
class Match(object):
    start = attrib(type=int, eq=True, hash=True)
    end = attrib(type=int, eq=True, hash=True)
    dist = attrib(type=int, eq=True, hash=True)
    matched = attrib(eq=False, hash=False)

    if __debug__:
        def __attrs_post_init__(self):
            if not (isinstance(self.start, int_types) and self.start >= 0):
                raise ValueError('start must be a non-negative integer')
            if not (isinstance(self.end, int_types) and self.end >= self.start):
                raise ValueError('end must be an integer no smaller than start')
            if not (isinstance(self.dist, int_types) and self.dist >= 0):
                print(self.dist)
                raise ValueError('dist must be a non-negative integer')
            if self.matched is None:
                raise ValueError('matched must be supplied')


@attrs(frozen=True, slots=True)
class LevenshteinSearchParams(object):
    """Parameter data-class for Levenshtein-distance fuzzy searches."""
    max_substitutions = attrib(default=None)
    max_insertions = attrib(default=None)
    max_deletions = attrib(default=None)
    max_l_dist = attrib(default=None)

    def __attrs_post_init__(self):
        self._check_params_valid()
        max_subs, max_ins, max_dels, max_l_dist = \
            self._normalize_params(*self.unpacked)
        object.__setattr__(self, 'max_substitutions', max_subs)
        object.__setattr__(self, 'max_insertions', max_ins)
        object.__setattr__(self, 'max_deletions', max_dels)
        object.__setattr__(self, 'max_l_dist', max_l_dist)

    @property
    def unpacked(self):
        return (
            self.max_substitutions,
            self.max_insertions,
            self.max_deletions,
            self.max_l_dist,
        )

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

    @classmethod
    def _normalize_params(cls,
                          max_substitutions, max_insertions,
                          max_deletions, max_l_dist):
        maxes_sum = sum(
            x if x is not None else 1 << 29
            for x in [
                max_substitutions,
                max_insertions,
                max_deletions,
            ]
        )

        if max_l_dist is None:
            # replace max_l_dist with the sum of the other limits
            return (
                max_substitutions,
                max_insertions,
                max_deletions,
                maxes_sum,
            )
        else:
            def _normalize(param):
                return min(param, max_l_dist) if param is not None else max_l_dist
            return (
                _normalize(max_substitutions),
                _normalize(max_insertions),
                _normalize(max_deletions),
                min(max_l_dist, maxes_sum),
            )


def count_differences_with_maximum(sequence1, sequence2, max_differences):
    n_different = 0
    for item1, item2 in zip(sequence1, sequence2):
        if item1 != item2:
            n_different += 1
            if n_different == max_differences:
                return n_different
    return n_different

try:
    from fuzzysearch._common import count_differences_with_maximum_byteslike
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
    """Get the longest match of those with the smallest distance."""
    return min(group, key=lambda match: (match.dist, -(match.end - match.start)))


def consolidate_overlapping_matches(matches):
    """Replace overlapping matches with a single, "best" match."""
    groups = group_matches(matches)
    best_matches = [get_best_match_in_group(group) for group in groups]
    return sorted(best_matches)


class FuzzySearchBase(object):
    """Abstract base class for fuzzy search classes"""
    @classmethod
    def search(cls, subsequence, sequence, search_params):
        raise NotImplementedError

    @classmethod
    def consolidate_matches(cls, matches):
        try:
            len(matches)
        except TypeError:
            return list(matches)
        else:
            return matches

    @classmethod
    def extra_items_for_chunked_search(cls, subsequence, search_params):
        raise NotImplementedError
