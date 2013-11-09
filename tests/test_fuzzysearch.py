from tests.compat import unittest
from fuzzysearch.fuzzysearch import find_near_matches, Match, _expand,\
    find_near_matches_with_ngrams, get_best_match_in_group, group_matches


class TestFuzzySearch(unittest.TestCase):
    def test_empty_sequence(self):
        self.assertEquals([], list(find_near_matches('PATTERN', '')))

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            list(find_near_matches('', 'TEXT'))

    def test_match_identical_sequence(self):
        matches = list(find_near_matches('PATTERN', 'PATTERN', max_l_dist=0))
        self.assertEquals([Match(start=0, end=len('PATTERN'), dist=0)], matches)

    def test_double_first_item(self):
        sequence = 'abcddefg'
        pattern = 'def'
        matches = list(find_near_matches(pattern, sequence, max_l_dist=1))
        self.assertIn(Match(start=4, end=7, dist=0), matches)
        #self.assertEquals([Match(start=4, end=7, dist=0)], matches)

    def test_missing_second_item(self):
        sequence = 'abcdefg'
        pattern = 'bde'
        matches = list(find_near_matches(pattern, sequence, max_l_dist=1))
        self.assertIn(Match(start=1, end=5, dist=1), matches)
        #self.assertEquals([Match(start=1, end=5, dist=1)], matches)

    def test_dna_search(self):
        # see: http://stackoverflow.com/questions/19725127/
        text = ''.join('''\
            GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGT
            CACACACACATTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACAC
            ATTAGACGCGTACATAGACACAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATAC
            TCGCGTAGTCGTGGGAGGCAAGGCACACAGGGGATAGG
            '''.split())
        pattern = 'TGCACTGTAGGGATAACAAT'

        matches = list(find_near_matches(pattern, text, max_l_dist=2))

        self.assertTrue(len(matches) > 0)
        self.assertIn(Match(start=3, end=24, dist=1), matches)

        #self.assertEquals(1, len(matches))


class TestExpand(unittest.TestCase):
    def test_identical(self):
        self.assertEquals((0, 3), _expand('abc', 'abc', 0))
        self.assertEquals((0, 3), _expand('abc', 'abc', 1))
        self.assertEquals((0, 3), _expand('abc', 'abc', 2))

    def test_one_missing(self):
        # first item missing
        self.assertEquals((1, 3), _expand('abcd', 'bcd', 1))
        self.assertEquals((1, 3), _expand('abcd', 'bcd', 2))

        # second item missing
        self.assertEquals((1, 3), _expand('abcd', 'acd', 1))
        self.assertEquals((1, 3), _expand('abcd', 'acd', 2))

        # last item missing
        self.assertEquals((1, 3), _expand('abcd', 'abc', 1))
        self.assertEquals((1, 3), _expand('abcd', 'abc', 2))

    def test_no_result(self):
        self.assertEquals((None, None), _expand('abc', 'def', 0))

    def test_one_extra(self):
        self.assertEquals((1, 3), _expand('abcd', 'abd', 1))
        self.assertEquals((1, 3), _expand('abcd', 'abd', 2))


class TestFuzzySearchBase(object):
    def search(self, subsequence, sequence, max_l_dist):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.assertEquals([], self.search('PATTERN', '', max_l_dist=0))

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT', max_l_dist=0)

    def test_match_identical_sequence(self):
        self.assertEquals(
            [Match(start=0, end=len('PATTERN'), dist=0)],
            self.search('PATTERN', 'PATTERN', max_l_dist=0),
        )

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        idx = text.find(substring)
        expected_match = Match(start=10, end=17, dist=0)

        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=0)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=1)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=2)
        )

    def test_double_first_item(self):
        self.assertEquals(
            [Match(start=4, end=7, dist=0)],
            self.search('def', 'abcddefg', max_l_dist=1),
        )

    def test_double_last_item(self):
        self.assertEquals(
            [Match(start=3, end=6, dist=0)],
            self.search('def', 'abcdeffg', max_l_dist=1),
        )

    def test_double_first_items(self):
        self.assertEquals(
            [Match(start=5, end=10, dist=0)],
            self.search('defgh', 'abcdedefghi', max_l_dist=3),
        )

    def test_double_last_items(self):
        self.assertEquals(
            [Match(start=3, end=8, dist=0)],
            self.search('defgh', 'abcdefghghi', max_l_dist=3),
        )

    def test_missing_second_item(self):
        self.assertEquals(
            [Match(start=1, end=5, dist=1)],
            self.search('bde', 'abcdefg', max_l_dist=1),
        )

    def test_missing_second_to_last_item(self):
        self.assertEquals(
            [Match(start=1, end=5, dist=1)],
            self.search('bce', 'abcdefg', max_l_dist=1),
        )

    def test_one_missing_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATERNaaaaaaaaa'
        expected_match = Match(start=10, end=16, dist=1)

        self.assertEquals(
            [],
            self.search(substring, text, max_l_dist=0)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=1)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=2)
        )

    def test_one_changed_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATtERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=1)

        self.assertEquals(
            [],
            self.search(substring, text, max_l_dist=0)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=1)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=2)
        )

    def test_one_extra_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTXERNaaaaaaaaa'
        expected_match = Match(start=10, end=18, dist=1)

        self.assertEquals(
            [],
            self.search(substring, text, max_l_dist=0)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=1)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=2)
        )

    def test_one_extra_repeating_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTTERNaaaaaaaaa'
        expected_match = Match(start=10, end=18, dist=1)

        self.assertEquals(
            [],
            self.search(substring, text, max_l_dist=0)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=1)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=2)
        )

    def test_one_extra_repeating_at_end(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=0)

        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=0)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=1)
        )
        self.assertEquals(
            [expected_match],
            self.search(substring, text, max_l_dist=2)
        )

    def test_one_missing_at_end_of_sequence(self):
        self.assertEquals(
            [Match(3, 6, 1)],
            self.search('defg', 'abcdef', max_l_dist=1)
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

        self.assertEquals(
            [Match(start=3, end=24, dist=1)],
            self.search(pattern, text, max_l_dist=2),
        )


class TestFindNearMatchesWithNgrams(TestFuzzySearchBase, unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return find_near_matches_with_ngrams(subsequence, sequence, max_l_dist)


class TestFindNearMatches(TestFuzzySearchBase, unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return [
            get_best_match_in_group(group)
            for group in group_matches(
                find_near_matches(subsequence, sequence, max_l_dist)
            )
        ]
