from tests.compat import unittest
from fuzzysearch.fuzzysearch import find_near_matches, Match


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
