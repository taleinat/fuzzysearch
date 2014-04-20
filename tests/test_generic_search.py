from tests.compat import unittest
from tests.test_levenshtein import TestFindNearMatchesLevenshteinBase
from fuzzysearch.common import Match, get_best_match_in_group, group_matches
from tests.test_substitutions_only import TestSubstitionsOnlyBase, \
    TestHasNearMatchSubstitionsOnly
from fuzzysearch.generic_search import \
    _find_near_matches_generic_linear_programming as fnm_generic_lp, \
    find_near_matches_generic_ngrams as fnm_generic_ngrams, \
    has_near_match_generic_ngrams as hnm_generic_ngrams


class TestGenericSearchLPAsLevenshtein(TestFindNearMatchesLevenshteinBase,
                                       unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return [
            get_best_match_in_group(group)
            for group in group_matches(
                fnm_generic_lp(subsequence, sequence, max_l_dist,
                               max_l_dist, max_l_dist, max_l_dist)
            )
        ]


class TestGenericSearchNgramsAsLevenshtein(TestFindNearMatchesLevenshteinBase,
                                       unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return fnm_generic_ngrams(subsequence, sequence, max_l_dist,
                                  max_l_dist, max_l_dist, max_l_dist)


class TestGenericSearchLPAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                             unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return list(
            fnm_generic_lp(subsequence, sequence, max_subs, 0, 0, max_subs)
        )


class TestGenericSearchNgramsAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                             unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return fnm_generic_ngrams(subsequence, sequence,
                                  max_subs, 0, 0, max_subs)


class TestGenericSearchBase(object):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.assertEqual(self.search('PATTERN', '', 0, 0, 0), [])

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT', 0, 0, 0)

    def test_match_identical_sequence(self):
        self.assertEqual(
            self.search('PATTERN', 'PATTERN', 0, 0, 0),
            [Match(start=0, end=len('PATTERN'), dist=0)],
        )

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=0)

        self.assertEqual(
            self.search(substring, text, 0, 0, 0),
            [expected_match],
        )

    def test_double_first_item(self):
        # sequence = 'abcdefg'
        # pattern = 'bde'

        self.assertEqual(
            self.search('def', 'abcddefg', 0, 0, 0),
            [Match(start=4, end=7, dist=0)],
        )

        self.assertEqual(
            self.search('def', 'abcddefg', 1, 0, 0),
            [Match(start=4, end=7, dist=0)],
        )

        self.assertListEqual(
            self.search('def', 'abcddefg', 0, 1, 0),
            [Match(start=3, end=7, dist=1), Match(start=4, end=7, dist=0)],
        )

        self.assertIn(
            Match(start=4, end=7, dist=0),
            self.search('def', 'abcddefg', 0, 0, 1),
        )

        self.assertEqual(
            self.search('def', 'abcddefg', 0, 1, 0, 0),
            [Match(start=4, end=7, dist=0)],
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

    def test_missing_second_item_complex(self):
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


class TestGenericSearchLP(TestGenericSearchBase, unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        return list(fnm_generic_lp(pattern, sequence,
                                   max_subs, max_ins, max_dels, max_l_dist))


class TestGenericSearchNgrams(TestGenericSearchBase, unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        return fnm_generic_ngrams(pattern, sequence,
                                  max_subs, max_ins, max_dels, max_l_dist)

    def test_missing_second_item_complex(self):
        pass


class TestHasNearMatchGenericNgramsAsSubstitutionsOnly(
    TestHasNearMatchSubstitionsOnly,
):
    def search(self, subsequence, sequence, max_subs):
        return hnm_generic_ngrams(subsequence, sequence,
                                  max_subs, 0, 0, max_subs)


class TestHasNearMatchGenericNgrams(TestGenericSearchBase, unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        return hnm_generic_ngrams(pattern, sequence,
                                  max_subs, max_ins, max_dels, max_l_dist)

    def assertEqual(self, actual_value, expected_value, *args, **kwargs):
        return super(TestHasNearMatchGenericNgrams, self).assertEqual(
            actual_value, bool(expected_value), *args, **kwargs)

    def assertListEqual(self, actual_value, expected_value, *args, **kwargs):
        return super(TestHasNearMatchGenericNgrams, self).assertEqual(
            actual_value, bool(expected_value), *args, **kwargs)

    def assertIn(self, member, container, *args, **kwargs):
        return super(TestHasNearMatchGenericNgrams, self).assertTrue(container)

    def test_missing_second_item_complex(self):
        self.assertTrue(self.search('bde', 'abcdefg', 1, 1, 1, 3))
