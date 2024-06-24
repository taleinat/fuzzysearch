import unittest

from fuzzysearch.common import group_matches, Match, get_best_match_in_group, \
    count_differences_with_maximum, consolidate_overlapping_matches
from fuzzysearch.substitutions_only import \
    has_near_match_substitutions as hnm_subs, \
    find_near_matches_substitutions as fnm_subs, \
    find_near_matches_substitutions_lp as fnm_subs_lp, \
    has_near_match_substitutions_lp as hnm_subs_lp, \
    find_near_matches_substitutions_ngrams as fnm_subs_ngrams, \
    has_near_match_substitutions_ngrams as hnm_subs_ngrams

from tests.compat import b
from tests.utils import skip_if_arguments_arent_byteslike


class TestSubstitionsOnlyBase(object):
    def search(self, subsequence, sequence, max_subs):
        raise NotImplementedError

    def expectedOutcomes(self, search_result, expected_outcomes, *args, **kwargs):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.expectedOutcomes(self.search(b('PATTERN'), b(''), max_subs=0), [])

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search(b(''), b('TEXT'), max_subs=0)

    def test_match_identical_sequence(self):
        self.expectedOutcomes(
            self.search(b('PATTERN'), b('PATTERN'), max_subs=0),
            [Match(start=0, end=len('PATTERN'), dist=0, matched=b('PATTERN'))],
        )

    def test_substring(self):
        substring = b('PATTERN')
        text = b('aaaaaaaaaaPATTERNaaaaaaaaa')
        expected_match = Match(start=10, end=17, dist=0, matched=b('PATTERN'))

        self.expectedOutcomes(
            self.search(substring, text, max_subs=0),
            [expected_match],
        )
        self.expectedOutcomes(
            self.search(substring, text, max_subs=1),
            [expected_match],
        )
        self.expectedOutcomes(
            self.search(substring, text, max_subs=2),
            [expected_match],
        )

    def test_double_first_item(self):
        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), max_subs=1),
            [Match(start=4, end=7, dist=0, matched=b('def'))],
        )

        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), max_subs=2),
            [Match(start=3, end=6, dist=2, matched=b('dde')),
             Match(start=4, end=7, dist=0, matched=b('def'))],
        )

    def test_two_identical(self):
        self.expectedOutcomes(
            self.search(b('abc'), b('abcabc'), max_subs=1),
            [Match(start=0, end=3, dist=0, matched=b('abc')),
             Match(start=3, end=6, dist=0, matched=b('abc'))],
        )

        self.expectedOutcomes(
            self.search(b('abc'), b('abcXabc'), max_subs=1),
            [Match(start=0, end=3, dist=0, matched=b('abc')),
             Match(start=4, end=7, dist=0, matched=b('abc'))],
        )

    def test_one_changed_in_middle(self):
        substring = b('abcdefg')
        pattern = b('abcXefg')
        expected_match = Match(start=0, end=7, dist=1, matched=pattern)

        self.expectedOutcomes(
            self.search(substring, pattern, max_subs=0),
            [],
        )

        self.expectedOutcomes(
            self.search(substring, pattern, max_subs=1),
            [expected_match],
        )

        self.expectedOutcomes(
            self.search(substring, pattern, max_subs=2),
            [expected_match],
        )

    def test_one_missing_in_middle(self):
        substring = b('PATTERN')
        text = b('aaaaaaaaaaPATERNaaaaaaaaa')

        for max_subs in [0, 1, 2]:
            self.expectedOutcomes(
                self.search(substring, text, max_subs=max_subs),
                [],
            )

    def test_one_changed_in_middle2(self):
        substring = b('PATTERN')
        text = b('aaaaaaaaaaPATtERNaaaaaaaaa')
        expected_match = Match(start=10, end=17, dist=1, matched=b('PATtERN'))

        self.expectedOutcomes(
            self.search(substring, text, max_subs=0),
            [],
        )
        self.expectedOutcomes(
            self.search(substring, text, max_subs=1),
            [expected_match],
        )
        self.expectedOutcomes(
            self.search(substring, text, max_subs=2),
            [expected_match],
        )

    def test_one_extra_in_middle(self):
        substring = b('PATTERN')
        text = b('aaaaaaaaaaPATTXERNaaaaaaaaa')

        for max_subs in [0, 1, 2]:
            self.expectedOutcomes(
                self.search(substring, text, max_subs=max_subs),
                [],
            )

    def test_all_different(self):
        substring = b('AAAA')
        text = b('ZZZZ')

        for max_subs in [0, 1, 2, 3]:
            self.expectedOutcomes(
                self.search(substring, text, max_subs=max_subs),
                [],
            )

        for max_subs in [4, 5]:
            self.expectedOutcomes(
                self.search(substring, text, max_subs=max_subs),
                [Match(start=0, end=4, dist=4, matched=b('ZZZZ'))],
            )

    def test_dna_search(self):
        # see: http://stackoverflow.com/questions/19725127/
        text = b(''.join('''\
            GACTAGCACTGTAGGGATAACAATTTCACACAGGTGGACAATTACATTGAAAATCACAGATTGGT
            CACACACACATTGGACATACATAGAAACACACACACATACATTAGATACGAACATAGAAACACAC
            ATTAGACGCGTACATAGACACAAACACATTGACAGGCAGTTCAGATGATGACGCCCGACTGATAC
            TCGCGTAGTCGTGGGAGGCAAGGCACACAGGGGATAGG
            '''.split()))
        pattern = b('TGCACTGTAGGGATAACAAT')

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=2),
            [Match(start=4, end=24, dist=1, matched=text[4:24])],
        )

    def test_protein_search1(self):
        # see:
        # * BioPython archives from March 14th, 2014
        #   http://lists.open-bio.org/pipermail/biopython/2014-March/009030.html
        # * https://github.com/taleinat/fuzzysearch/issues/3
        text = b(''.join('''\
            XXXXXXXXXXXXXXXXXXXGGGTTVTTSSAAAAAAAAAAAAAGGGTTLTTSSAAAAAAAAAAAA
            AAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBGGGTTLTTSS
        '''.split()))
        pattern = b("GGGTTLTTSS")

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=0),
            [Match(start=42, end=52, dist=0, matched=text[42:52]),
             Match(start=99, end=109, dist=0, matched=text[99:109])],
        )

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=1),
            [Match(start=19, end=29, dist=1, matched=text[19:29]),
             Match(start=42, end=52, dist=0, matched=text[42:52]),
             Match(start=99, end=109, dist=0, matched=text[99:109])],
        )

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=2),
            [Match(start=19, end=29, dist=1, matched=text[19:29]),
             Match(start=42, end=52, dist=0, matched=text[42:52]),
             Match(start=99, end=109, dist=0, matched=text[99:109])],
        )

    def test_protein_search2(self):
        # see:
        # * BioPython archives from March 14th, 2014
        #   http://lists.open-bio.org/pipermail/biopython/2014-March/009030.html
        # * https://github.com/taleinat/fuzzysearch/issues/3
        text = b(''.join('''\
            XXXXXXXXXXXXXXXXXXXGGGTTVTTSSAAAAAAAAAAAAAGGGTTVTTSSAAAAAAAAAAA
            AAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBGGGTTLTTSS
        '''.split()))
        pattern = b("GGGTTLTTSS")

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=0),
            [Match(start=99, end=109, dist=0, matched=text[99:109])],
        )

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=1),
            [Match(start=19, end=29, dist=1, matched=text[19:29]),
             Match(start=42, end=52, dist=1, matched=text[42:52]),
             Match(start=99, end=109, dist=0, matched=text[99:109])],
        )

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=2),
            [Match(start=19, end=29, dist=1, matched=text[19:29]),
             Match(start=42, end=52, dist=1, matched=text[42:52]),
             Match(start=99, end=109, dist=0, matched=text[99:109])],
        )

    def test_missing_at_beginning(self):
        self.expectedOutcomes(
            self.search(b("ATTEST"), b("TESTOSTERONE"), max_subs=2),
            [],
        )

    def test_unicode_substring(self):
        pattern = '\u03A3\u0393'
        text = '\u03A0\u03A3\u0393\u0394'
        self.expectedOutcomes(
            self.search(pattern, text, max_subs=0),
            [Match(1, 3, 0, matched=text[1:3])]
        )

    def test_max_substitutions_gte_subseq_len(self):
        for max_subs in [1, 2, 5]:
            self.expectedOutcomes(
                self.search(b('b'), b('abc'), max_subs),
                [Match(0, 1, 1, b('a')),
                 Match(1, 2, 0, b('b')),
                 Match(2, 3, 1, b('c'))]
            )
        for extra_subs in [0, 1, 7]:
            self.expectedOutcomes(
                self.search(b('PATTERN'), b('PATTERN'), len('PATTERN') + extra_subs),
                [Match(0, len('PATTERN'), 0, b('PATTERN'))]
            )


class TestFindNearMatchesSubstitions(TestSubstitionsOnlyBase,
                                     unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return fnm_subs(subsequence, sequence, max_subs)

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
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


class TestFindNearMatchesSubstitionsLinearProgramming(TestSubstitionsOnlyBase,
                                                      unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return list(fnm_subs_lp(subsequence, sequence, max_subs))

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        return self.assertEqual(search_results, expected_outcomes, *args, **kwargs)


class TestFindNearMatchesSubstitionsNgrams(TestSubstitionsOnlyBase,
                                           unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        if max_subs >= len(subsequence):
            self.skipTest("avoiding calling fnm_subs_ngrams() " +
                          "with max_subs >= len(subsequence)")
        return fnm_subs_ngrams(subsequence, sequence, max_subs)

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        return self.assertEqual(
            consolidate_overlapping_matches(search_results),
            consolidate_overlapping_matches(expected_outcomes),
            *args, **kwargs)


class TestHasNearMatchSubstitionsOnlyBase(TestSubstitionsOnlyBase):
    def search(self, subsequence, sequence, max_subs):
        raise NotImplementedError

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        return self.assertEqual(bool(search_results),
                                bool(expected_outcomes),
                                *args, **kwargs)


class TestHasNearMatchSubstitionsOnly(TestHasNearMatchSubstitionsOnlyBase,
                                      unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return hnm_subs(subsequence, sequence, max_subs)


class TestHasNearMatchSubstitionsOnlyNgrams(TestHasNearMatchSubstitionsOnlyBase,
                                            unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        if max_subs >= len(subsequence):
            self.skipTest("avoiding calling hnm_subs_ngrams() " +
                          "with max_subs >= len(subsequence)")
        return hnm_subs_ngrams(subsequence, sequence, max_subs)


class TestHasNearMatchSubstitionsOnlyLp(TestHasNearMatchSubstitionsOnlyBase,
                                        unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return hnm_subs_lp(subsequence, sequence, max_subs)


try:
    from fuzzysearch._substitutions_only import \
        substitutions_only_has_near_matches_lp_byteslike as \
            hnm_subs_lp_byteslike, \
        substitutions_only_find_near_matches_lp_byteslike as \
            fnm_subs_lp_byteslike, \
        substitutions_only_has_near_matches_ngrams_byteslike as \
            hnm_subs_ngrams_byteslike, \
        substitutions_only_find_near_matches_ngrams_byteslike as \
            fnm_subs_ngrams_byteslike
except ImportError:
    pass
else:
    class TestHasNearMatchesSubstitionsLpByteslike(
            TestHasNearMatchSubstitionsOnlyBase,
            unittest.TestCase
    ):
        @skip_if_arguments_arent_byteslike
        def search(self, subsequence, sequence, max_subs):
            return hnm_subs_lp_byteslike(subsequence, sequence,
                                         max_subs)

    class TestHasNearMatchesSubstitionsNgramsByteslike(
            TestHasNearMatchSubstitionsOnlyBase,
            unittest.TestCase
    ):
        @skip_if_arguments_arent_byteslike
        def search(self, subsequence, sequence, max_subs):
            if max_subs >= len(subsequence):
                self.skipTest("avoiding calling hnm_subs_ngrams_byteslike() " +
                              "with max_subs >= len(subsequence)")
            return hnm_subs_ngrams_byteslike(subsequence, sequence,
                                             max_subs)

    class TestFindNearMatchesSubstitionsLpByteslike(
            TestSubstitionsOnlyBase,
            unittest.TestCase
    ):
        @skip_if_arguments_arent_byteslike
        def search(self, subsequence, sequence, max_subs):
            results = fnm_subs_lp_byteslike(subsequence, sequence,
                                            max_subs)
            matches = [
                Match(
                    index,
                    index + len(subsequence),
                    count_differences_with_maximum(
                        sequence[index:index+len(subsequence)],
                        subsequence,
                        max_subs + 1,
                    ),
                    matched=sequence[index:index+len(subsequence)]
                )
                for index in results
            ]
            return matches

        def expectedOutcomes(self, search_results, expected_outcomes,
                             *args, **kwargs):
            return self.assertEqual(search_results, expected_outcomes,
                                    *args, **kwargs)

    class TestFindNearMatchesSubstitionsNgramsByteslike(
            TestSubstitionsOnlyBase,
            unittest.TestCase
    ):
        @skip_if_arguments_arent_byteslike
        def search(self, subsequence, sequence, max_subs):
            results = fnm_subs_ngrams_byteslike(subsequence, sequence,
                                                max_subs)
            matches = [
                Match(
                    index,
                    index + len(subsequence),
                    count_differences_with_maximum(
                        sequence[index:index+len(subsequence)],
                        subsequence,
                        max_subs + 1,
                    ),
                    matched=sequence[index:index+len(subsequence)]
                )
                for index in results
            ]
            return [
                get_best_match_in_group(group)
                for group in group_matches(matches)
            ]

        def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
            return self.assertEqual(
                consolidate_overlapping_matches(search_results),
                consolidate_overlapping_matches(expected_outcomes),
                *args, **kwargs)
