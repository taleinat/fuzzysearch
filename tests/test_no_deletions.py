import unittest

from fuzzysearch.common import Match, LevenshteinSearchParams
from fuzzysearch.no_deletions import _expand, \
    find_near_matches_no_deletions_ngrams
from tests.test_substitutions_only import TestFindNearMatchesSubstitionsNgrams


def fnm_nodels_ngrams(sequence, subsequence, max_substitutions, max_insertions, max_l_dist=None):
    return find_near_matches_no_deletions_ngrams(
        sequence, subsequence, LevenshteinSearchParams(
            max_substitutions, max_insertions, 0, max_l_dist,
        )
    )


class TestExpand(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(_expand('abc', 'abc', 0, 0, 0), [(0, 0)])

    def test_startswith(self):
        self.assertEqual(_expand('abc', 'abcdef', 0, 0, 0), [(0, 0)])
        self.assertEqual(_expand('abc', 'abcdef', 1, 0, 1), [(0, 0)])
        self.assertEqual(_expand('abc', 'abcdef', 2, 0, 2), [(0, 0)])
        self.assertEqual(_expand('abc', 'abcdef', 0, 1, 1), [(0, 0)])
        self.assertEqual(_expand('abc', 'abcdef', 0, 2, 2), [(0, 0)])
        self.assertEqual(_expand('abc', 'abcdef', 1, 1, 1), [(0, 0)])
        self.assertEqual(_expand('abc', 'abcdef', 1, 1, 2), [(0, 0)])
        self.assertEqual(_expand('abc', 'abcdef', 2, 2, 2), [(0, 0)])

    def test_one_missing(self):
        # first item missing
        self.assertEqual(_expand('abcd', 'bcd---', 0, 1, 1), [])
        self.assertEqual(_expand('abcd', 'bcd---', 1, 0, 1), [])
        self.assertEqual(_expand('abcd', 'bcd---', 1, 1, 2), [])

        # second item missing
        self.assertEqual(_expand('abcd', 'acd---', 0, 1, 1), [])
        self.assertEqual(_expand('abcd', 'acd---', 1, 0, 1), [])
        self.assertEqual(_expand('abcd', 'acd---', 1, 1, 2), [])

        # last item missing
        self.assertEqual(_expand('abcd', 'abc---', 0, 1, 1), [])
        self.assertEqual(_expand('abcd', 'abc---', 1, 0, 1), [(1, 0)])
        self.assertEqual(_expand('abcd', 'abc---', 1, 1, 2), [(1, 0)])

    def test_no_result(self):
        self.assertEqual(_expand('abc', 'def', 0, 0, 0), [])
        self.assertEqual(_expand('abc', 'defg', 1, 1, 1), [])
        self.assertEqual(_expand('abc', 'defg', 1, 1, 2), [])

    def test_one_extra(self):
        # extra first item
        self.assertEqual(_expand('bcd', 'abcd', 0, 0, 0), [])
        self.assertEqual(_expand('bcd', 'abcd', 0, 1, 1), [(0, 1)])

        # extra third item
        self.assertEqual(_expand('abd', 'abcd', 0, 0, 0), [])
        self.assertEqual(_expand('abd', 'abcd', 0, 1, 1), [(0, 1)])

        # extra last item
        self.assertEqual(_expand('abc', 'abcd', 0, 0, 0), [(0, 0)])
        self.assertEqual(_expand('abc', 'abcd', 0, 1, 1), [(0, 0)])

    def test_insert_and_substitute(self):
        self.assertEqual(_expand('abcdefg', 'abc-def----', 1, 1, 2), [(1, 1)])
        self.assertEqual(_expand('abcdefg', 'abc-def----', 1, 1, 1), [])
        self.assertEqual(_expand('abcdefg', 'abc-def----', 1, 0, 1), [])
        self.assertEqual(_expand('abcdefg', 'abc-def----', 0, 1, 1), [])

    def test_double_first_item(self):
        self.assertEqual(_expand('abc', 'aabc', 1, 1, 1), [(0, 1)])

    def test_two_insertions(self):
        self.assertEqual(_expand('abc', 'a--bc', 0, 2, 2), [(0, 2)])
        self.assertEqual(_expand('abc', 'a--bc', 2, 0, 2), [(2, 0)])
        self.assertEqual(_expand('abc', 'a--bc', 2, 2, 2), [(2, 0), (0, 2)])
        self.assertEqual(_expand('abc', 'a--bc', 1, 1, 2), [])


class TestFindNearMatchesNoDeletionsNgramsAsNoSubstituions(
    TestFindNearMatchesSubstitionsNgrams, unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        if max_subs >= len(subsequence):
            self.skipTest("avoiding calling fnm_no_deletions_ngrams() " +
                          "with max_subs >= len(subsequence)")
        return fnm_nodels_ngrams(subsequence, sequence, max_subs, 0)


class TestFindNearMatchesNoDeletionsNgrams(unittest.TestCase):
    def test_one_sub_one_ins(self):
        sequence = 'abcdefghij'
        pattern = 'bceXghi'
        expected_match = Match(start=1, end=9, dist=2, matched=sequence[1:9])
        self.assertEqual(fnm_nodels_ngrams(pattern, sequence, 0, 0, 0), [])
        self.assertEqual(fnm_nodels_ngrams(pattern, sequence, 0, 1, 2), [])
        self.assertEqual(fnm_nodels_ngrams(pattern, sequence, 1, 0, 2), [])
        self.assertEqual(fnm_nodels_ngrams(pattern, sequence, 1, 1, 1), [])
        self.assertEqual(
            fnm_nodels_ngrams(pattern, sequence, 1, 1, 2),
            [expected_match],
        )

    def test_two_extra(self):
        sequence = '--abc--de--'
        pattern = 'abcde'

        self.assertEqual(
            fnm_nodels_ngrams(pattern, sequence, 0, 2, 2),
            [Match(start=2, end=9, dist=2, matched=sequence[2:9])],
        )

        self.assertEqual(
            fnm_nodels_ngrams(pattern, sequence, 2, 0, 2),
            [Match(start=2, end=7, dist=2, matched=sequence[2:7])],
        )

        self.assertEqual(
            fnm_nodels_ngrams(pattern, sequence, 2, 2, 2),
            [Match(start=2, end=7, dist=2, matched=sequence[2:7]),
             Match(start=2, end=9, dist=2, matched=sequence[2:9])],
        )
