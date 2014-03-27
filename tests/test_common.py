from fuzzysearch.common import Match, group_matches, GroupOfMatches, \
    search_exact
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


import six

class TestSearchExact(unittest.TestCase):
    def search(self, sequence, subsequence):
        return list(search_exact(sequence, subsequence))

    def test_bytes(self):
        text = six.b('abc')
        self.assertEqual(self.search(text, text), [0])

    def test_unicode(self):
        text = six.u('abc')
        self.assertEqual(self.search(text, text), [0])

    def test_biopython_Seq(self):
        try:
            from Bio.Seq import Seq
        except ImportError:
            raise unittest.SkipTest('Test requires BioPython')
        else:
            self.assertEqual(self.search(Seq('abc'), Seq('abc')), [0])

    def test_empty_sequence(self):
        self.assertEqual(self.search('PATTERN', ''), [])

    def test_empty_subsequence(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT')

    def test_match_identical_sequence(self):
        self.assertEqual(self.search('PATTERN', 'PATTERN'), [0])

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        self.assertEqual(self.search(substring, text), [10])

    def test_double_first_item(self):
        self.assertEqual(self.search('def', 'abcddefg'), [4])

    def test_missing_second_item(self):
        self.assertEqual(self.search('bde', 'abcdefg'), [])

    def test_completely_different(self):
        self.assertEqual(self.search('abc', 'def'), [])

    def test_startswith(self):
        self.assertEqual(self.search('abc', 'abcd'), [0])

    def test_endswith(self):
        self.assertEqual(self.search('bcd', 'abcd'), [1])
