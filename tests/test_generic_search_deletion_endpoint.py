import unittest

from fuzzysearch import Match, find_near_matches
from fuzzysearch.common import LevenshteinSearchParams
from fuzzysearch.generic_search import (
    _find_near_matches_generic_linear_programming,
    find_near_matches_generic_ngrams,
)


class TestGenericSearchDeletionEndpoint(unittest.TestCase):
    def test_deletions_preserve_last_matching_character(self):
        for pattern, sequence in [('xyz', 'wz'), (b'xyz', b'wz')]:
            with self.subTest(pattern=pattern):
                self.assertEqual(
                    find_near_matches(pattern, sequence,
                                      max_substitutions=0, max_insertions=0,
                                      max_l_dist=2),
                    [Match(1, 2, 2, sequence[1:2])],
                )

    def test_endpoint_in_middle_of_sequence(self):
        params = LevenshteinSearchParams(0, 0, 1, 1)
        matches = list(_find_near_matches_generic_linear_programming(
            'abc', 'xabx', params))
        self.assertIn(Match(1, 3, 1, 'ab'), matches)
        matches = list(_find_near_matches_generic_linear_programming(
            'abc', 'xacx', params))
        self.assertIn(Match(1, 3, 1, 'ac'), matches)

    def test_ngram_search_preserves_last_matching_character(self):
        params = LevenshteinSearchParams(0, 0, 1, 1)
        matches = list(find_near_matches_generic_ngrams(
            'abcdefg', 'xabcdfgx', params))
        self.assertIn(Match(1, 7, 1, 'abcdfg'), matches)
