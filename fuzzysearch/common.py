import sys
from collections import namedtuple


__all__ = [
    'Match', 'Ngram',
    'search_exact',
    'group_matches', 'get_best_match_in_group',
]


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


def search_exact(subsequence, sequence, start_index=0, end_index=None):
    if isinstance(sequence, CLASSES_WITH_FIND):
        find = sequence.find
    else:
        raise TypeError('unsupported sequence type: %s' % type(sequence))

    if not subsequence:
        raise ValueError('subsequence must not be empty')

    index = find(subsequence, start_index, end_index)
    while index >= 0:
        yield index
        index = find(subsequence, index + 1, end_index)


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
