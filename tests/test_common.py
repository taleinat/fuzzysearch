from fuzzysearch.common import Match, group_matches, GroupOfMatches
from tests.compat import unittest


class TestGroupOfMatches(unittest.TestCase):
    def test_is_match_in_group(self):
        match = Match(2, 4, 0)
        group = GroupOfMatches(match)
        self.assertTrue(group.is_match_in_group(match))
        self.assertTrue(group.is_match_in_group(Match(2, 4, 0)))


class TestGroupMatches(unittest.TestCase):
    def test_separate(self):
        matches = [
            Match(start=19, end=29, dist=1),
            Match(start=42, end=52, dist=1),
            Match(start=99, end=109, dist=0),
        ]
        self.assertListEqual(
            group_matches(matches),
            [set([m]) for m in matches],
        )

    def test_separate_with_duplicate(self):
        matches = [
            Match(start=19, end=29, dist=1),
            Match(start=42, end=52, dist=1),
            Match(start=99, end=109, dist=0),
        ]
        self.assertListEqual(
            group_matches(matches + [matches[1]]),
            [set([m]) for m in matches],
        )
