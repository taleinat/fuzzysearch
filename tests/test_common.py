import unittest

from fuzzysearch.common import Match, group_matches, GroupOfMatches, \
    count_differences_with_maximum
from tests.compat import b


class TestGroupOfMatches(unittest.TestCase):
    def test_is_match_in_group(self):
        match = Match(2, 4, 0, 'matched')
        group = GroupOfMatches(match)
        self.assertTrue(group.is_match_in_group(match))
        self.assertTrue(group.is_match_in_group(Match(2, 4, 0, 'matched')))


class TestGroupMatches(unittest.TestCase):
    def test_separate(self):
        matches = [
            Match(start=19, end=29, dist=1, matched='x'*10),
            Match(start=42, end=52, dist=1, matched='x'*10),
            Match(start=99, end=109, dist=0, matched='x'*10),
        ]
        self.assertEqual(
            group_matches(matches),
            [{m} for m in matches],
        )

    def test_separate_with_duplicate(self):
        matches = [
            Match(start=19, end=29, dist=1, matched='x'*10),
            Match(start=42, end=52, dist=1, matched='x'*10),
            Match(start=99, end=109, dist=0, matched='x'*10),
        ]
        self.assertEqual(
            group_matches(matches + [matches[1]]),
            [{m} for m in matches],
        )


class TestCountDifferencesWithMaximumBase(object):
    def count_diffs(self, seq1, seq2, max_diffs):
        raise NotImplementedError

    def test_empty(self):
        result = self.count_diffs('', '', 1)
        self.assertEqual(result, 0)

    def test_identical_one_character(self):
        result = self.count_diffs('a', 'a', 1)
        self.assertEqual(result, 0)

    def test_identical_word(self):
        result = self.count_diffs('word', 'word', 1)
        self.assertEqual(result, 0)

    def test_identical_long(self):
        result = self.count_diffs('long'*10, 'long'*10, 1)
        self.assertEqual(result, 0)

    def test_different_less_than_max(self):
        result = self.count_diffs('abc', 'def', 4)
        self.assertEqual(result, 3)

    def test_different_more_than_max(self):
        result = self.count_diffs('abc', 'def', 2)
        self.assertEqual(result, 2)

    def test_partially_different_in_middle(self):
        result = self.count_diffs('abcdef', 'a--d-f', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs('abcdef', 'a--d-f', 2)
        self.assertEqual(result, 2)

    def test_partially_different_at_start(self):
        result = self.count_diffs('abcdef', '--c-ef', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs('abcdef', '--c-ef', 2)
        self.assertEqual(result, 2)

    def test_partially_different_at_end(self):
        result = self.count_diffs('abcdef', 'ab-d--', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs('abcdef', 'ab-d--', 2)
        self.assertEqual(result, 2)


class TestCountDifferencesWithMaximum(TestCountDifferencesWithMaximumBase,
                                      unittest.TestCase):
    def count_diffs(self, seq1, seq2, max_diffs):
        return count_differences_with_maximum(seq1, seq2, max_diffs)


try:
    from fuzzysearch._common import count_differences_with_maximum_byteslike
except ImportError:
    pass
else:
    class TestCountDifferencesWithMaximumByteslike(
            TestCountDifferencesWithMaximumBase, unittest.TestCase):
        def count_diffs(self, seq1, seq2, max_diffs):
            return count_differences_with_maximum_byteslike(b(seq1), b(seq2),
                                                            max_diffs)
