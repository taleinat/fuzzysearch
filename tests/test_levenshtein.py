from tests.compat import unittest, mock

from fuzzysearch.common import Match, get_best_match_in_group, group_matches
from fuzzysearch.levenshtein import find_near_matches_levenshtein, \
    find_near_matches_levenshtein_linear_programming as fnm_levenshtein_lp
from fuzzysearch.levenshtein_ngram import _expand, \
    find_near_matches_levenshtein_ngrams as fnm_levenshtein_ngrams


class TestFuzzySearch(unittest.TestCase):
    def test_empty_sequence(self):
        self.assertEqual(
            list(fnm_levenshtein_lp('PATTERN', '', max_l_dist=0)),
            [],
        )

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            list(fnm_levenshtein_lp('', 'TEXT', max_l_dist=0))

    def test_match_identical_sequence(self):
        matches = \
            list(fnm_levenshtein_lp('PATTERN', 'PATTERN', max_l_dist=0))
        self.assertEqual(matches, [Match(start=0, end=len('PATTERN'), dist=0)])

    def test_double_first_item(self):
        sequence = 'abcddefg'
        pattern = 'def'
        matches = \
            list(fnm_levenshtein_lp(pattern, sequence, max_l_dist=1))
        self.assertIn(Match(start=4, end=7, dist=0), matches)
        #self.assertEqual([Match(start=4, end=7, dist=0)], matches)

    def test_missing_second_item(self):
        sequence = 'abcdefg'
        pattern = 'bde'
        matches = \
            list(fnm_levenshtein_lp(pattern, sequence, max_l_dist=1))
        self.assertIn(Match(start=1, end=5, dist=1), matches)
        #self.assertEqual([Match(start=1, end=5, dist=1)], matches)

    def test_dna_search(self):
        # see: http://stackoverflow.com/questions/19725127/
        text = ''.join('''\
            GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGT
            CACACACACATTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACAC
            ATTAGACGCGTACATAGACACAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATAC
            TCGCGTAGTCGTGGGAGGCAAGGCACACAGGGGATAGG
            '''.split())
        pattern = 'TGCACTGTAGGGATAACAAT'

        matches = list(fnm_levenshtein_lp(pattern, text, max_l_dist=2))

        self.assertTrue(len(matches) > 0)
        self.assertIn(Match(start=3, end=24, dist=1), matches)


class TestExpand(unittest.TestCase):
    def test_both_empty(self):
        self.assertEqual(_expand('', '', 0), (0, 0))

    def test_empty_subsequence(self):
        self.assertEqual(_expand('', 'TEXT', 0), (0, 0))

    def test_empty_sequence(self):
        self.assertEqual(_expand('PATTERN', '', 0), (None, None))

    def test_identical(self):
        self.assertEqual(_expand('abc', 'abc', 0), (0, 3))
        self.assertEqual(_expand('abc', 'abc', 1), (0, 3))
        self.assertEqual(_expand('abc', 'abc', 2), (0, 3))

    def test_first_item_missing(self):
        self.assertEqual(_expand('abcd', 'bcd', 0), (None, None))
        self.assertEqual(_expand('abcd', 'bcd', 1), (1, 3))
        self.assertEqual(_expand('abcd', 'bcd', 2), (1, 3))

    def test_second_item_missing(self):
        self.assertEqual(_expand('abcd', 'acd', 0), (None, None))
        self.assertEqual(_expand('abcd', 'acd', 1), (1, 3))
        self.assertEqual(_expand('abcd', 'acd', 2), (1, 3))

    def test_second_before_last_item_missing(self):
        self.assertEqual(_expand('abcd', 'abd', 0), (None, None))
        self.assertEqual(_expand('abcd', 'abd', 1), (1, 3))
        self.assertEqual(_expand('abcd', 'abd', 2), (1, 3))

    def test_last_item_missing(self):
        self.assertEqual(_expand('abcd', 'abc', 0), (None, None))
        self.assertEqual(_expand('abcd', 'abc', 1), (1, 3))
        self.assertEqual(_expand('abcd', 'abc', 2), (1, 3))

    def test_completely_different(self):
        self.assertEqual(_expand('abc', 'def', 0), (None, None))

    def test_startswith(self):
        self.assertEqual(_expand('abc', 'abcd', 0), (0, 3))
        self.assertEqual(_expand('abc', 'abcd', 1), (0, 3))
        self.assertEqual(_expand('abc', 'abcd', 2), (0, 3))


class TestFindNearMatchesLevenshteinBase(object):
    def search(self, subsequence, sequence, max_l_dist):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.assertEqual(self.search('PATTERN', '', max_l_dist=0), [])

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT', max_l_dist=0)

    def test_match_identical_sequence(self):
        self.assertEqual(
            self.search('PATTERN', 'PATTERN', max_l_dist=0),
            [Match(start=0, end=len('PATTERN'), dist=0)],
        )

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=0)

        self.assertEqual(
            self.search(substring, text, max_l_dist=1),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=0),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=2),
            [expected_match],
        )

    def test_double_first_item(self):
        self.assertEqual(
            self.search('def', 'abcddefg', max_l_dist=1),
            [Match(start=4, end=7, dist=0)],
        )

    def test_double_last_item(self):
        self.assertEqual(
            self.search('def', 'abcdeffg', max_l_dist=1),
            [Match(start=3, end=6, dist=0)],
        )

    def test_double_first_items(self):
        self.assertEqual(
            self.search('defgh', 'abcdedefghi', max_l_dist=3),
            [Match(start=5, end=10, dist=0)],
        )

    def test_double_last_items(self):
        self.assertEqual(
            self.search('cdefgh', 'abcdefghghi', max_l_dist=3),
            [Match(start=2, end=8, dist=0)],
        )

    def test_missing_second_item(self):
        self.assertEqual(
            self.search('bde', 'abcdefg', max_l_dist=1),
            [Match(start=1, end=5, dist=1)],
        )

    def test_missing_second_to_last_item(self):
        self.assertEqual(
            self.search('bce', 'abcdefg', max_l_dist=1),
            [Match(start=1, end=5, dist=1)],
        )

        self.assertEqual(
            self.search('bce', 'abcdefg', max_l_dist=2),
            [Match(start=1, end=5, dist=1)],
        )

    def test_one_missing_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATERNaaaaaaaaa'
        expected_match = Match(start=10, end=16, dist=1)

        self.assertEqual(
            self.search(substring, text, max_l_dist=0),
            [],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=1),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=2),
            [expected_match],
        )

    def test_one_changed_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATtERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=1)

        self.assertEqual(
            self.search(substring, text, max_l_dist=0),
            [],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=1),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=2),
            [expected_match],
        )

    def test_one_extra_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTXERNaaaaaaaaa'
        expected_match = Match(start=10, end=18, dist=1)

        self.assertEqual(
            self.search(substring, text, max_l_dist=0),
            [],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=1),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=2),
            [expected_match],
        )

    def test_one_extra_repeating_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTTERNaaaaaaaaa'
        expected_match = Match(start=10, end=18, dist=1)

        self.assertEqual(
            self.search(substring, text, max_l_dist=0),
            [],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=1),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=2),
            [expected_match],
        )

    def test_one_extra_repeating_at_end(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=0)

        self.assertEqual(
            self.search(substring, text, max_l_dist=0),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=1),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_l_dist=2),
            [expected_match],
        )

    def test_one_missing_at_end_of_sequence(self):
        self.assertEqual(
            self.search('defg', 'abcdef', max_l_dist=1),
            [Match(3, 6, 1)],
        )

    def test_dna_search(self):
        # see: http://stackoverflow.com/questions/19725127/
        text = ''.join('''\
            GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGT
            CACACACACATTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACAC
            ATTAGACGCGTACATAGACACAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATAC
            TCGCGTAGTCGTGGGAGGCAAGGCACACAGGGGATAGG
            '''.split())
        pattern = 'TGCACTGTAGGGATAACAAT'

        self.assertEqual(
            self.search(pattern, text, max_l_dist=2),
            [Match(start=3, end=24, dist=1)],
        )

    def test_protein_search1(self):
        # see:
        # * BioPython archives from March 14th, 2014
        #   http://lists.open-bio.org/pipermail/biopython/2014-March/009030.html
        # * https://github.com/taleinat/fuzzysearch/issues/3
        text = ''.join('''\
            XXXXXXXXXXXXXXXXXXXGGGTTVTTSSAAAAAAAAAAAAAGGGTTLTTSSAAAAAAAAAAAA
            AAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBGGGTTLTTSS
        '''.split())
        pattern = "GGGTTLTTSS"

        self.assertListEqual(
            self.search(pattern, text, max_l_dist=2),
            [Match(start=19, end=29, dist=1),
             Match(start=42, end=52, dist=0),
             Match(start=99, end=109, dist=0)],
        )

    def test_protein_search2(self):
        # see:
        # * BioPython archives from March 14th, 2014
        #   http://lists.open-bio.org/pipermail/biopython/2014-March/009030.html
        # * https://github.com/taleinat/fuzzysearch/issues/3
        text = ''.join('''\
            XXXXXXXXXXXXXXXXXXXGGGTTVTTSSAAAAAAAAAAAAAGGGTTVTTSSAAAAAAAAAAA
            AAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBGGGTTLTTSS
        '''.split())
        pattern = "GGGTTLTTSS"

        self.assertListEqual(
            self.search(pattern, text, max_l_dist=2),
            [Match(start=19, end=29, dist=1),
             Match(start=42, end=52, dist=1),
             Match(start=99, end=109, dist=0)],
        )


class TestFindNearMatchesLevenshteinNgrams(TestFindNearMatchesLevenshteinBase,
                                           unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return fnm_levenshtein_ngrams(subsequence, sequence, max_l_dist)


class TestFindNearMatchesLevenshteinLP(TestFindNearMatchesLevenshteinBase,
                                       unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return [
            get_best_match_in_group(group)
            for group in group_matches(
                fnm_levenshtein_lp(subsequence, sequence, max_l_dist)
            )
        ]


class TestFindNearMatchesLevenshtein(TestFindNearMatchesLevenshteinBase,
                                     unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return find_near_matches_levenshtein(subsequence, sequence, max_l_dist)

    def test_fallback_to_search_exact(self):
        with mock.patch('fuzzysearch.levenshtein.search_exact') \
                as mock_search_exact:
            mock_search_exact.return_value = [7]
            matches = find_near_matches_levenshtein('a', 'b' * 10, 0)
            self.assertGreater(mock_search_exact.call_count, 0)
            self.assertEqual(matches, [Match(7, 8, 0)])
