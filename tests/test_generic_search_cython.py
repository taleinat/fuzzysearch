import unittest

from tests.compat import b
from tests.utils import skip_if_arguments_arent_byteslike
from tests.test_levenshtein import TestFindNearMatchesLevenshteinBase
from fuzzysearch.common import Match, get_best_match_in_group, group_matches, LevenshteinSearchParams
from tests.test_substitutions_only import TestSubstitionsOnlyBase
from tests.test_generic_search import TestGenericSearchBase


try:
    from fuzzysearch._generic_search import \
        c_find_near_matches_generic_linear_programming as c_fnm_generic_lp, \
        c_find_near_matches_generic_ngrams as c_fnm_generic_ngrams
except ImportError:
    pass
else:
    class TestGenericSearchLpAsLevenshtein(TestFindNearMatchesLevenshteinBase,
                                           unittest.TestCase):
        @skip_if_arguments_arent_byteslike
        def search(self, subsequence, sequence, max_l_dist):
            return [
                get_best_match_in_group(group)
                for group in group_matches(
                    c_fnm_generic_lp(subsequence,
                                     sequence,
                                     LevenshteinSearchParams(max_l_dist, max_l_dist, max_l_dist, max_l_dist))
                )
            ]

    class TestGenericSearchNgramsAsLevenshtein(
        TestFindNearMatchesLevenshteinBase, unittest.TestCase):
        @skip_if_arguments_arent_byteslike
        def search(self, subsequence, sequence, max_l_dist):
            if max_l_dist >= len(subsequence):
                self.skipTest("avoiding calling c_fnm_generic_ngrams() " +
                              "with max_l_dist >= len(subsequence)")
            return [
                get_best_match_in_group(group)
                for group in group_matches(
                    c_fnm_generic_ngrams(subsequence,
                                         sequence,
                                         LevenshteinSearchParams(max_l_dist, max_l_dist, max_l_dist, max_l_dist))
                )
            ]


    class TestGenericSearchLpAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                                 unittest.TestCase):
        @skip_if_arguments_arent_byteslike
        def search(self, subsequence, sequence, max_subs):
            return list(
                c_fnm_generic_lp(subsequence,
                                 sequence,
                                 LevenshteinSearchParams(max_subs, 0, 0, max_subs))
            )

        def expectedOutcomes(self, search_results, expected_outcomes,
                             *args, **kwargs):
            return self.assertEqual(search_results, expected_outcomes,
                                    *args, **kwargs)


    class TestGenericSearchNgramsAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                                     unittest.TestCase):
        @skip_if_arguments_arent_byteslike
        def search(self, subsequence, sequence, max_subs):
            if max_subs >= len(subsequence):
                self.skipTest("avoiding calling c_fnm_generic_ngrams() " +
                              "with max_subs >= len(subsequence)")
            return [
                get_best_match_in_group(group)
                for group in group_matches(
                    c_fnm_generic_ngrams(subsequence,
                                         sequence,
                                         LevenshteinSearchParams(max_subs, 0, 0, max_subs))
                )
        ]

        def expectedOutcomes(self, search_results, expected_outcomes,
                             *args, **kwargs):
            best_from_grouped_results = [
                get_best_match_in_group(group)
                for group in group_matches(search_results)
            ]
            best_from_grouped_exepected_outcomes = [
                get_best_match_in_group(group)
                for group in group_matches(expected_outcomes)
            ]
            return self.assertEqual(best_from_grouped_results,
                                    best_from_grouped_exepected_outcomes,
                                    *args, **kwargs)


    class TestGenericSearchLp(TestGenericSearchBase, unittest.TestCase):
        @skip_if_arguments_arent_byteslike
        def search(self, pattern, sequence, max_subs, max_ins, max_dels,
                   max_l_dist=None):
            return list(c_fnm_generic_lp(pattern,
                                         sequence,
                                         LevenshteinSearchParams(
                                             max_subs, max_ins,
                                             max_dels, max_l_dist,
                                         )))

        def expectedOutcomes(self, search_result, expected_outcomes,
                             *args, **kwargs):
            self.assertEqual(search_result, expected_outcomes, *args, **kwargs)

        def test_double_first_item_two_results(self):
            self.assertEqual(
                self.search(b('def'), b('abcddefg'), 0, 1, 0),
                [Match(start=3, end=7, dist=1, matched=b('ddef')),
                 Match(start=4, end=7, dist=0, matched=b('def'))],
            )

        def test_missing_second_item_complex(self):
            self.assertEqual(
                self.search(b('bde'), b('abcdefg'), 1, 1, 1, 1),
                [Match(start=1, end=5, dist=1, matched=b('bcde')),
                 Match(start=2, end=5, dist=1, matched=b('cde')),
                 Match(start=3, end=5, dist=1, matched=b('de'))],
            )

            self.assertTrue(
                {
                    Match(start=1, end=5, dist=1, matched=b('bcde')),
                    Match(start=2, end=5, dist=1, matched=b('cde')),
                    Match(start=3, end=5, dist=1, matched=b('de')),
                    Match(start=2, end=5, dist=2, matched=b('bcd')),
                }.issubset(set(
                    self.search(b('bde'), b('abcdefg'), 1, 1, 1, 3),
                ))
            )

    class TestGenericSearchNgrams(TestGenericSearchBase, unittest.TestCase):
        @skip_if_arguments_arent_byteslike
        def search(self, pattern, sequence, max_subs, max_ins, max_dels,
                   max_l_dist=None):
            return [
                get_best_match_in_group(group)
                for group in group_matches(
                    c_fnm_generic_ngrams(pattern,
                                         sequence,
                                         LevenshteinSearchParams(
                                             max_subs, max_ins,
                                             max_dels, max_l_dist,
                                         ))
                )
            ]

        def expectedOutcomes(self, search_result, expected_outcomes,
                             *args, **kwargs):
            best_from_groups = [
                get_best_match_in_group(group)
                for group in group_matches(search_result)
            ]
            self.assertEqual(search_result, best_from_groups, *args, **kwargs)

        def test_missing_second_item_complex(self):
            self.assertTrue(
                set(self.search(b('bde'), b('abcdefg'), 1, 1, 1, 1)).issubset([
                    Match(start=1, end=5, dist=1, matched=b('bcde')),
                    Match(start=2, end=5, dist=1, matched=b('cde')),
                    Match(start=3, end=5, dist=1, matched=b('de')),
                ])
            )
