import re
import unittest

from fuzzysearch.common import Match, consolidate_overlapping_matches
from fuzzysearch.levenshtein import find_near_matches_levenshtein, \
    find_near_matches_levenshtein_linear_programming as fnm_levenshtein_lp
from fuzzysearch.levenshtein_ngram import \
    _expand, _py_expand_short, _expand_long, \
    find_near_matches_levenshtein_ngrams as fnm_levenshtein_ngrams


def longstr(string):
    return re.sub(r'\s+', '', string)


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
        self.assertEqual(matches, [Match(start=0, end=len('PATTERN'), dist=0,
                                         matched='PATTERN')])

    def test_double_first_item(self):
        sequence = 'abcddefg'
        pattern = 'def'
        matches = \
            list(fnm_levenshtein_lp(pattern, sequence, max_l_dist=1))
        self.assertIn(Match(start=4, end=7, dist=0, matched=pattern), matches)

    def test_missing_second_item(self):
        sequence = 'abcdefg'
        pattern = 'bde'
        matches = \
            list(fnm_levenshtein_lp(pattern, sequence, max_l_dist=1))
        self.assertIn(Match(start=1, end=5, dist=1, matched='bcde'), matches)

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
        self.assertIn(Match(start=3, end=24, dist=1, matched=text[3:24]),
                      matches)


class TestExpandBase(object):
    expand = None  # override in sub-classes!

    def test_both_empty(self):
        self.assertEqual(self.expand('', '', 0), (0, 0))

    def test_empty_subsequence(self):
        self.assertEqual(self.expand('', 'TEXT', 0), (0, 0))

    def test_empty_sequence(self):
        self.assertEqual(self.expand('PATTERN', '', 0), (None, None))
        self.assertEqual(self.expand('PATTERN', '', 6), (None, None))
        self.assertEqual(self.expand('PATTERN', '', 7), (7, 0))
        self.assertEqual(self.expand('PATTERN', '', 8), (7, 0))

    def test_identical(self):
        self.assertEqual(self.expand('abc', 'abc', 0), (0, 3))
        self.assertEqual(self.expand('abc', 'abc', 1), (0, 3))
        self.assertEqual(self.expand('abc', 'abc', 2), (0, 3))

    def test_first_item_missing(self):
        self.assertEqual(self.expand('abcd', 'bcd', 0), (None, None))
        self.assertEqual(self.expand('abcd', 'bcd', 1), (1, 3))
        self.assertEqual(self.expand('abcd', 'bcd', 2), (1, 3))

    def test_second_item_missing(self):
        self.assertEqual(self.expand('abcd', 'acd', 0), (None, None))
        self.assertEqual(self.expand('abcd', 'acd', 1), (1, 3))
        self.assertEqual(self.expand('abcd', 'acd', 2), (1, 3))

    def test_second_before_last_item_missing(self):
        self.assertEqual(self.expand('abcd', 'abd', 0), (None, None))
        self.assertEqual(self.expand('abcd', 'abd', 1), (1, 3))
        self.assertEqual(self.expand('abcd', 'abd', 2), (1, 3))

    def test_last_item_missing(self):
        self.assertEqual(self.expand('abcd', 'abc', 0), (None, None))
        self.assertEqual(self.expand('abcd', 'abc', 1), (1, 3))
        self.assertEqual(self.expand('abcd', 'abc', 2), (1, 3))

    def test_completely_different(self):
        self.assertEqual(self.expand('abc', 'def', 0), (None, None))

    def test_startswith(self):
        self.assertEqual(self.expand('abc', 'abcd', 0), (0, 3))
        self.assertEqual(self.expand('abc', 'abcd', 1), (0, 3))
        self.assertEqual(self.expand('abc', 'abcd', 2), (0, 3))

    def test_missing_at_start_middle_and_end(self):
        self.assertEqual(self.expand('abcd', '-ab-cd-', 0), (None, None))
        self.assertEqual(self.expand('abcd', '-ab-cd-', 1), (None, None))
        self.assertEqual(self.expand('abcd', '-ab-cd-', 2), (2, 6))
        self.assertEqual(self.expand('abcd', '-ab-cd-', 3), (2, 6))

    def test_no_common_chars(self):
        self.assertEqual(self.expand('abc', 'de', 2), (None, None))
        self.assertEqual(self.expand('abc', 'de', 3)[0], 3)
        self.assertEqual(self.expand('abc', 'de', 4)[0], 3)

    def test_long_needle(self):
        self.assertEqual(
            self.expand('abcdefghijklmnop', 'abcdefg-hijk-mnopqrst', 0),
            (None, None),
        )
        self.assertEqual(
            self.expand('abcdefghijklmnop', 'abcdefg-hijk-mnopqrst', 1),
            (None, None),
        )
        self.assertEqual(
            self.expand('abcdefghijklmnop', 'abcdefg-hijk-mnopqrst', 2),
            (2, 17),
        )
        self.assertEqual(
            self.expand('abcdefghijklmnop', 'abcdefg-hijk-mnopqrst', 3),
            (2, 17),
        )

        self.assertEqual(
            self.expand('abcdefghijklmnop', 'abcdefg-hijk-mnop', 3),
            (2, 17),
        )

        self.assertEqual(
            self.expand('abcdefghijklmnop', '-bcdefg-hijk-mnop', 3),
            (3, 17),
        )
        self.assertEqual(
            self.expand('abcdefghijklmnop', '-abcdefg-hijk-mnop', 3),
            (3, 18),
        )

        self.assertEqual(
            self.expand('abcdefghijklmnop', 'abc---defg-hijk-mnopqrst', 8),
            (5, 20),
        )


class TestExpand(TestExpandBase, unittest.TestCase):
    expand = staticmethod(_expand)


class TestPyExpandShort(TestExpandBase, unittest.TestCase):
    expand = staticmethod(_py_expand_short)


try:
    from fuzzysearch._levenshtein_ngrams import c_expand_short
except ImportError:
    pass
else:
    class TestCExpandShort(TestExpandBase, unittest.TestCase):
        expand = staticmethod(c_expand_short)


class TestExpandLong(TestExpandBase, unittest.TestCase):
    expand = staticmethod(_expand_long)


class TestFindNearMatchesLevenshteinBase(object):
    def search(self, subsequence, sequence, max_l_dist):
        raise NotImplementedError
    
    test_cases_data = {
        # name: (needle, haystack, [
        #   (max_l_dist, [(start, end, dist), ...]),
        # ])
        'identical sequence': ('PATTERN', 'PATTERN', [
            (0, [(0, 7, 0)]),
        ]),
        'substring': ('PATTERN', '----------PATTERN---------', [
            (0, [(10, 17, 0)]),
            (1, [(10, 17, 0)]),
            (2, [(10, 17, 0)]),
        ]),
        'double first item': ('def', 'abcddefg', [
            (1, [(4, 7, 0)]),
        ]),
        'double last item': ('def', 'abcdeffg', [
            (1, [(3, 6, 0)]),
        ]),
        'double first items': ('defgh', 'abcdedefghi', [
            (3, [(5, 10, 0)]),
        ]),
        'double last items': ('cdefgh', 'abcdefghghi', [
            (3, [(2, 8, 0)]),
        ]),
        'missing second item': ('bde', 'abcdefg', [
            (1, [(1, 5, 1)]),
        ]),
        'missing second to last item': ('bce', 'abcdefg', [
            (1, [(1, 5, 1)]),
            (2, [(1, 5, 1)]),
        ]),
        'one missing in middle': ('PATTERN', '----------PATERN---------', [
            (0, []),
            (1, [(10, 16, 1)]),
            (2, [(10, 16, 1)]),
        ]),
        'one changed in middle': ('PATTERN', '----------PAT-ERN---------', [
            (0, []),
            (1, [(10, 17, 1)]),
            (2, [(10, 17, 1)]),
        ]),
        'one extra in middle': ('PATTERN', '----------PATT-ERN---------', [
            (0, []),
            (1, [(10, 18, 1)]),
            (2, [(10, 18, 1)]),
        ]),
        'one extra repeating in middle': ('PATTERN', '----------PATTTERN---------', [
            (0, []),
            (1, [(10, 18, 1)]),
            (2, [(10, 18, 1)]),
        ]),
        'one extra repeating at end': ('PATTERN', '----------PATTERNN---------', [
            (0, [(10, 17, 0)]),
            (1, [(10, 17, 0)]),
            (2, [(10, 17, 0)]),
        ]),
        'one missing at end': ('defg', 'abcdef', [
            (1, [(3, 6, 1)]),
        ]),
        'highly repetetive': ('a' * 9, 'a' * 7 + 'xx', [
            (1, []),
            (2, [(0, 9, 2)]),
        ]),
        'DNA search': (
            'TGCACTGTAGGGATAACAAT',
            longstr('''
                GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTG
                GTCACACACACATTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAAC
                ACACATTAGACGCGTACATAGACACAAACACATTGACAGGCAGTTCAGATGATGACGCCCGAC
                TGATACTCGCGTAGTCGTGGGAGGCAAGGCACACAGGGGATAGG
            '''),
            [
                (2, [(3, 24, 1)]),
            ]
        ),
        # see:
        # * BioPython archives from March 14th, 2014
        #   http://lists.open-bio.org/pipermail/biopython/2014-March/009030.html
        # * https://github.com/taleinat/fuzzysearch/issues/3
        'protein search 1': (
            'GGGTTLTTSS',
            longstr('''
                XXXXXXXXXXXXXXXXXXXGGGTTVTTSSAAAAAAAAAAAAAGGGTTLTTSSAAAAAAAAAAA
                AAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBGGGTTLTTSS
            '''),
            [
                (0, [(42, 52, 0), (99, 109, 0)]),
                (1, [(19, 29, 1), (42, 52, 0), (99, 109, 0)]),
                (2, [(19, 29, 1), (42, 52, 0), (99, 109, 0)]),
            ]
        ),
        'protein search 2': (
            'GGGTTLTTSS',
            longstr('''
                XXXXXXXXXXXXXXXXXXXGGGTTVTTSSAAAAAAAAAAAAAGGGTTVTTSSAAAAAAAAAAA
                AAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBGGGTTLTTSS
            '''),
            [
                (0, [(99, 109, 0)]),
                (1, [(19, 29, 1), (42, 52, 1), (99, 109, 0)]),
                (2, [(19, 29, 1), (42, 52, 1), (99, 109, 0)]),
            ]
        ),
        'list of words': (
            "over a lazy dog".split(),
            "the big brown fox jumped over the lazy dog".split(),
            [
                (0, []),
                (1, [(5, 9, 1)]),
                (2, [(5, 9, 1)]),
            ]
        ),
    }

    def test_cases(self):
        for name, data in self.test_cases_data.items():
            substring, text, max_l_dist2expected_matches = data
            with self.subTest(name=name):
                for max_l_dist, expected_matches in max_l_dist2expected_matches:
                    self.assertEqual(
                        self.search(substring, text, max_l_dist=max_l_dist),
                        [Match(*x, matched=text[x[0]:x[1]])
                         for x in expected_matches],
                    )

    def test_empty_sequence(self):
        self.assertEqual(self.search('PATTERN', '', max_l_dist=0), [])

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT', max_l_dist=0)

    def test_all_different(self):
        for max_l_dist in [0, 1, 2, 3]:
            self.assertEqual(
                self.search('AAAA', 'ZZZZ', max_l_dist),
                [],
            )

        matches = self.search('AAAA', 'ZZZZ', max_l_dist=4)
        self.assertGreater(len(matches), 0)
        self.assertTrue(all(match.dist == 4 for match in matches))


class TestFindNearMatchesLevenshteinNgrams(TestFindNearMatchesLevenshteinBase,
                                           unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        if max_l_dist >= len(subsequence):
            self.skipTest(
                'skipping ngram search with max_l_dist >= len(subsequence)')
        return consolidate_overlapping_matches(
            fnm_levenshtein_ngrams(subsequence, sequence, max_l_dist)
        )


class TestFindNearMatchesLevenshteinLP(TestFindNearMatchesLevenshteinBase,
                                       unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return consolidate_overlapping_matches(
            fnm_levenshtein_lp(subsequence, sequence, max_l_dist)
        )


class TestFindNearMatchesLevenshtein(TestFindNearMatchesLevenshteinBase,
                                     unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return consolidate_overlapping_matches(
            find_near_matches_levenshtein(subsequence, sequence, max_l_dist)
        )
