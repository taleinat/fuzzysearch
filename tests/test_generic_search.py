from tests.compat import unittest
from tests.test_levenshtein import TestFindNearMatchesLevenshteinBase
from fuzzysearch.common import Match, get_best_match_in_group, group_matches
from fuzzysearch.generic_search import \
    find_near_matches_generic_linear_programming as fnm_generic_lp, \
    has_near_match_generic_ngrams
from tests.test_substitutions_only import TestSubstitionsOnlyBase, \
    TestHasNearMatchSubstitionsOnly


class TestGenericSearchAsLevenshtein(TestFindNearMatchesLevenshteinBase,
                                     unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return [
            get_best_match_in_group(group)
            for group in group_matches(
                fnm_generic_lp(subsequence, sequence, max_l_dist,
                               max_l_dist, max_l_dist, max_l_dist)
            )
        ]


class TestGenericSearchAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                           unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return list(
            fnm_generic_lp(subsequence, sequence, max_subs, 0, 0, max_subs)
        )


class TestGenericSearch(unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        return list(fnm_generic_lp(pattern, sequence, max_subs,
                                   max_ins, max_dels, max_l_dist))

    def test_empty_sequence(self):
        self.assertEqual([], self.search('PATTERN', '', 0, 0, 0))

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT', 0, 0, 0)

    def test_match_identical_sequence(self):
        self.assertEqual(
            [Match(start=0, end=len('PATTERN'), dist=0)],
            self.search('PATTERN', 'PATTERN', 0, 0, 0),
        )

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=0)

        self.assertEqual(
            [expected_match],
            self.search(substring, text, 0, 0, 0)
        )

    def test_double_first_item(self):
        # sequence = 'abcdefg'
        # pattern = 'bde'

        self.assertEqual(
            [Match(start=4, end=7, dist=0)],
            self.search('def', 'abcddefg', 0, 0, 0),
        )

        self.assertEqual(
            [Match(start=4, end=7, dist=0)],
            self.search('def', 'abcddefg', 1, 0, 0),
        )

        self.assertListEqual(
            [Match(start=3, end=7, dist=1), Match(start=4, end=7, dist=0)],
            self.search('def', 'abcddefg', 0, 1, 0),
        )

        self.assertIn(
            Match(start=4, end=7, dist=0),
            self.search('def', 'abcddefg', 0, 0, 1),
        )

        self.assertEqual(
            [Match(start=4, end=7, dist=0)],
            self.search('def', 'abcddefg', 0, 1, 0, 0),
        )

    def test_missing_second_item(self):
        # sequence = 'abcdefg'
        # pattern = 'bde'

        self.assertEqual(
            self.search('bde', 'abcdefg', 0, 1, 0),
            [Match(start=1, end=5, dist=1)],
        )

        self.assertEqual(
            self.search('bde', 'abcdefg', 0, 0, 0),
            [],
        )

        self.assertEqual(
            self.search('bde', 'abcdefg', 1, 0, 0),
            [Match(start=2, end=5, dist=1)],
        )

        self.assertEqual(
            self.search('bde', 'abcdefg', 0, 0, 1),
            [Match(start=3, end=5, dist=1)],
        )

        self.assertListEqual(
            self.search('bde', 'abcdefg', 1, 1, 1, 1),
            [Match(start=1, end=5, dist=1),
             Match(start=2, end=5, dist=1),
             Match(start=3, end=5, dist=1)],
        )

        self.assertTrue(
            set([
                Match(start=1, end=5, dist=1),
                Match(start=2, end=5, dist=1),
                Match(start=3, end=5, dist=1),
                Match(start=2, end=5, dist=3),
            ]).issubset(set(
                self.search('bde', 'abcdefg', 1, 1, 1, 3),
            ))
        )

    def test_argument_handling(self):
        # check that no exception is raised when some values are None
        self.assertEqual(
            self.search('a', 'b', 0, None, None, None),
            [],
        )

        self.assertEqual(
            self.search('a', 'b', None, 0, None, None),
            [],
        )

        self.assertEqual(
            self.search('a', 'b', None, None, 0, None),
            [],
        )

        self.assertEqual(
            self.search('a', 'b', None, None, None, 0),
            [],
        )


class TestHasNearMatchGenericNgramsAsSubstitutionsOnly(
    TestHasNearMatchSubstitionsOnly,
):
    def search(self, subsequence, sequence, max_subs):
        return has_near_match_generic_ngrams(subsequence, sequence,
                                             max_subs, 0, 0, max_subs)

    def test_one_changed_in_middle(self):
        self.assertTrue(self.search('abcdefg', 'abcXefg', 1))
