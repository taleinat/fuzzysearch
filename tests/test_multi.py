from tests.compat import unittest

from fuzzysearch.common import get_best_match_in_group, group_matches,\
    LevenshteinSearchParams, Match
from fuzzysearch.multi import find_near_matches_multiple

from tests.test_generic_search import TestGenericSearchBase


class TestMultiSearch(unittest.TestCase):
    def search(self, patterns, sequences, search_params):
        return find_near_matches_multiple(patterns, sequences,
                                          search_params.max_substitutions,
                                          search_params.max_insertions,
                                          search_params.max_deletions,
                                          search_params.max_l_dist)

    def test_empty_inputs(self):
        self.assertEqual([], self.search([], [],
                                         LevenshteinSearchParams(1, 1, 1, 1)))
        self.assertEqual([], self.search(['needle'], [],
                                         LevenshteinSearchParams(1, 1, 1, 1)))
        self.assertEqual([[]], self.search([], ['haystack'],
                                           LevenshteinSearchParams(1, 1, 1, 1)))

    def test_multi_identical(self):
        """Search for two different strings, in both of them."""
        needles = ["foo", "bar"]
        haystacks = needles

        for max_l_dist in [0, 1, 2]:
            with self.subTest(max_l_dist=max_l_dist):
                search_params = LevenshteinSearchParams(max_l_dist, max_l_dist,
                                                        max_l_dist, max_l_dist)
                self.assertEqual(
                    [[[Match(0, 3, 0)], []],
                     [[], [Match(0, 3, 0)]]],
                    self.search(needles, haystacks, search_params)
                )

    def test_multi_different(self):
        """Search for two different strings, in variations of both of them."""
        needles = ["foo", "bar"]
        haystacks = ["fuo", "ber"]

        for max_l_dist in [0]:
            with self.subTest(max_l_dist=max_l_dist):
                search_params = LevenshteinSearchParams(max_l_dist, max_l_dist,
                                                        max_l_dist, max_l_dist)
                self.assertEqual(
                    [[[], []],
                     [[], []]],
                    self.search(needles, haystacks, search_params)
                )

        for max_l_dist in [1, 2]:
            with self.subTest(max_l_dist=max_l_dist):
                search_params = LevenshteinSearchParams(max_l_dist, max_l_dist,
                                                        max_l_dist, max_l_dist)
                self.assertEqual(
                    [[[Match(0, 3, 1)], []],
                     [[], [Match(0, 3, 1)]]],
                    self.search(needles, haystacks, search_params)
                )

    def test_multi_random(self):
        """Search for random sub-strings of random strings.

        Each sub-string is searched for in all of the random strings.
        """
        import random

        rand = random.Random()
        rand.seed(1)
        randint = rand.randint
        texts = [
            ''.join(
                chr(randint(0, 255))
                for _i in range(randint(1000, 10000))
            )
            for _n_text in range(10)
        ]

        needles = []
        for n_text, text in enumerate(texts):
            for needle_len in [4, 7, 10, 15, 50]:
                index = randint(0, len(text) - needle_len + 1)
                sub_text = text[index:index + needle_len]
                needles.append((n_text, index, sub_text))

        for max_l_dist in [0, 1]:
            with self.subTest(max_l_dist=max_l_dist):
                search_params = LevenshteinSearchParams(max_l_dist, max_l_dist,
                                                        max_l_dist, max_l_dist)
                needle_strs = [needle for (n_text, index, needle) in needles]
                results = self.search(needle_strs,
                                      texts,
                                      search_params)
                for n_needle, (n_text, index, needle) in enumerate(needles):
                    self.assertIn(Match(index, index + len(needle), 0), results[n_text][n_needle])

        for max_l_dist in [2]:
            with self.subTest(max_l_dist=max_l_dist):
                search_params = LevenshteinSearchParams(max_l_dist, max_l_dist,
                                                        max_l_dist, max_l_dist)
                needles2 = [
                    (n_text, index, needle)
                    for (n_text, index, needle) in needles
                    if len(needle) >= 6
                ]
                needle_strs = [needle for (n_text, index, needle) in needles2]
                results = self.search(needle_strs,
                                      texts,
                                      search_params)
                for n_needle, (n_text, index, needle) in enumerate(needles2):
                    self.assertIn(Match(index, index + len(needle), 0), results[n_text][n_needle])

    def test_identical_needles(self):
        """Search for a single needle multiple times."""
        for search_params in [
            LevenshteinSearchParams(0, 0, 0, 0),
            LevenshteinSearchParams(0, 1, 0, 1),
            LevenshteinSearchParams(0, 0, 1, 1),
        ]:
            with self.subTest(search_params=search_params):
                self.assertEqual(
                    self.search(
                        ['abc'] * 3,
                        ['--abc-----adc--', '---------xyz----'],
                        search_params=search_params,
                    ),
                    [[[Match(2, 5, 0)]] * 3,
                     [[]] * 3],
                )

        for search_params in [
            LevenshteinSearchParams(1, 1, 1, 1),
            LevenshteinSearchParams(1, 0, 0, 1),
            # deletion + insertion = substitution
            LevenshteinSearchParams(0, 1, 1, 1),
        ]:
            with self.subTest(search_params=search_params):
                self.assertEqual(
                    self.search(
                        ['abc'] * 3,
                        ['--abc-----adc--', '---------xyz----'],
                        search_params=search_params,
                    ),
                    [[[Match(2, 5, 0), Match(10, 13, 1)]] * 3,
                     [[]] * 3],
                )


class TestMultiSearchAsGenericSearch(unittest.TestCase, TestGenericSearchBase):
    def search(self, pattern, sequence,
               max_subs, max_ins, max_dels, max_l_dist=None):
        results = find_near_matches_multiple([pattern], [sequence],
                                             max_subs, max_ins,
                                             max_dels, max_l_dist)
        return results[0][0]

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        best_from_grouped_exepected_outcomes = [
            get_best_match_in_group(group)
            for group in group_matches(expected_outcomes)
        ]
        return self.assertEqual(search_results,
                                best_from_grouped_exepected_outcomes)
