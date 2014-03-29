from fuzzysearch.susbstitutions_only import \
    find_near_matches_substitutions_linear_programming as fnm_subs_lp, \
    find_near_matches_substitutions_ngrams as fnm_subs_ngrams, \
    has_near_match_substitutions_ngrams
from tests.compat import unittest

from fuzzysearch.common import Match


class TestSubstitionsOnlyBase(object):
    def search(self, subsequence, sequence, max_subs):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.assertEqual(self.search('PATTERN', '', max_subs=0), [])

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT', max_subs=0)

    def test_match_identical_sequence(self):
        self.assertEqual(
            self.search('PATTERN', 'PATTERN', max_subs=0),
            [Match(start=0, end=len('PATTERN'), dist=0)],
        )

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=0)

        self.assertEqual(
            self.search(substring, text, max_subs=0),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_subs=1),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_subs=2),
            [expected_match],
        )

    def test_double_first_item(self):
        self.assertListEqual(
            self.search('def', 'abcddefg', max_subs=1),
            [Match(start=4, end=7, dist=0)],
        )

        self.assertListEqual(
            self.search('def', 'abcddefg', max_subs=2),
            [Match(start=3, end=6, dist=2),
             Match(start=4, end=7, dist=0)],
        )

    def test_two_identical(self):
        self.assertEqual(
            self.search('abc', 'abcabc', max_subs=1),
            [Match(start=0, end=3, dist=0), Match(start=3, end=6, dist=0)],
        )

        self.assertEqual(
            self.search('abc', 'abcXabc', max_subs=1),
            [Match(start=0, end=3, dist=0), Match(start=4, end=7, dist=0)],
        )

    def test_one_changed_in_middle(self):
        substring = 'abcdefg'
        pattern = 'abcXefg'
        expected_match = Match(start=0, end=7, dist=1)

        self.assertEqual(
            self.search(substring, pattern, max_subs=0),
            [],
        )

        self.assertEqual(
            self.search(substring, pattern, max_subs=1),
            [expected_match],
        )

        self.assertEqual(
            self.search(substring, pattern, max_subs=2),
            [expected_match],
        )

    def test_one_missing_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATERNaaaaaaaaa'

        for max_subs in [0, 1, 2]:
            self.assertEquals(
                self.search(substring, text, max_subs=max_subs),
                [],
            )

    def test_one_changed_in_middle2(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATtERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=1)

        self.assertEqual(
            self.search(substring, text, max_subs=0),
            [],
        )
        self.assertEqual(
            self.search(substring, text, max_subs=1),
            [expected_match],
        )
        self.assertEqual(
            self.search(substring, text, max_subs=2),
            [expected_match],
        )

    def test_one_extra_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTXERNaaaaaaaaa'

        for max_subs in [0, 1, 2]:
            self.assertEquals(
                self.search(substring, text, max_subs=max_subs),
                [],
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
            self.search(pattern, text, max_subs=2),
            [Match(start=4, end=24, dist=1)],
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
            self.search(pattern, text, max_subs=0),
            [Match(start=42, end=52, dist=0),
             Match(start=99, end=109, dist=0)],
        )

        self.assertListEqual(
            self.search(pattern, text, max_subs=1),
            [Match(start=19, end=29, dist=1),
             Match(start=42, end=52, dist=0),
             Match(start=99, end=109, dist=0)],
        )

        self.assertListEqual(
            self.search(pattern, text, max_subs=2),
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
            self.search(pattern, text, max_subs=0),
            [Match(start=99, end=109, dist=0)],
        )

        self.assertListEqual(
            self.search(pattern, text, max_subs=1),
            [Match(start=19, end=29, dist=1),
             Match(start=42, end=52, dist=1),
             Match(start=99, end=109, dist=0)],
        )

        self.assertListEqual(
            self.search(pattern, text, max_subs=2),
            [Match(start=19, end=29, dist=1),
             Match(start=42, end=52, dist=1),
             Match(start=99, end=109, dist=0)],
        )

    def test_missing_at_beginning(self):
        self.assertEqual(
            self.search("ATTEST", "TESTOSTERONE", max_subs=2),
            [],
        )


class TestFindNearMatchesSubstitionsLinearProgramming(TestSubstitionsOnlyBase, unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return list(fnm_subs_lp(subsequence, sequence, max_subs))


class TestFindNearMatchesSubstitionsNgrams(TestSubstitionsOnlyBase, unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return fnm_subs_ngrams(subsequence, sequence, max_subs)


class TestHasNearMatchSubstitionsOnly(unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return has_near_match_substitutions_ngrams(subsequence, sequence, max_subs)

    def test_empty_sequence(self):
        self.assertFalse(self.search('PATTERN', '', max_subs=0))

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT', max_subs=0)

    def test_match_identical_sequence(self):
        self.assertTrue(self.search('PATTERN', 'PATTERN', max_subs=0))

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        for max_subs in [0, 1, 2]:
            self.assertTrue(self.search(substring, text, max_subs))

    def test_double_first_item(self):
        for max_subs in [0, 1, 2]:
            self.assertTrue(self.search('def', 'abcddefg', max_subs))

    def test_two_identical(self):
        for max_subs in [0, 1, 2]:
            self.assertTrue(self.search('abc', 'abcabc', max_subs))
            self.assertTrue(self.search('abc', 'abcXabc', max_subs))

    def test_one_changed_in_middle(self):
        self.assertFalse(self.search('abcdefg', 'abcXefg', 0))
        self.assertTrue(self.search('abcdefg', 'abcXefg', 1))
        self.assertTrue(self.search('abcdefg', 'abcXefg', 2))

    def test_one_missing_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATERNaaaaaaaaa'

        for max_subs in [0, 1, 2]:
            self.assertFalse(self.search(substring, text, max_subs=max_subs))

    def test_one_changed_in_middle2(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATtERNaaaaaaaaa'

        self.assertFalse(self.search(substring, text, max_subs=0))
        self.assertTrue(self.search(substring, text, max_subs=1))
        self.assertTrue(self.search(substring, text, max_subs=2))

    def test_one_extra_in_middle(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTXERNaaaaaaaaa'

        for max_subs in [0, 1, 2]:
            self.assertFalse(self.search(substring, text, max_subs=max_subs))

    def test_dna_search(self):
        # see: http://stackoverflow.com/questions/19725127/
        text = ''.join('''\
            GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGT
            CACACACACATTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACAC
            ATTAGACGCGTACATAGACACAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATAC
            TCGCGTAGTCGTGGGAGGCAAGGCACACAGGGGATAGG
            '''.split())
        pattern = 'TGCACTGTAGGGATAACAAT'

        self.assertTrue(self.search(pattern, text, max_subs=2))

    def test_missing_at_beginning(self):
        self.assertFalse(self.search("ATTEST", "TESTOSTERONE", max_subs=2))
