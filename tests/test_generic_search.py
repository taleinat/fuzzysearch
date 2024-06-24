import unittest

from tests.compat import b
from tests.test_levenshtein import TestFindNearMatchesLevenshteinBase
from fuzzysearch.common import Match, get_best_match_in_group, group_matches, LevenshteinSearchParams, consolidate_overlapping_matches
from tests.test_substitutions_only import TestSubstitionsOnlyBase, \
    TestHasNearMatchSubstitionsOnlyBase
from fuzzysearch.generic_search import \
    _find_near_matches_generic_linear_programming as fnm_generic_lp, \
    find_near_matches_generic_ngrams as fnm_generic_ngrams, \
    has_near_match_generic_ngrams as hnm_generic_ngrams, \
    find_near_matches_generic


class TestGenericSearchLpAsLevenshtein(TestFindNearMatchesLevenshteinBase,
                                       unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        search_params = LevenshteinSearchParams(max_l_dist, max_l_dist,
                                                max_l_dist, max_l_dist)
        return consolidate_overlapping_matches(
            fnm_generic_lp(subsequence, sequence, search_params)
        )


class TestGenericSearchNgramsAsLevenshtein(TestFindNearMatchesLevenshteinBase,
                                           unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        if max_l_dist >= len(subsequence):
            self.skipTest("avoiding calling fnm_generic_ngrams() " +
                          "with max_l_dist >= len(subsequence)")
        search_params = LevenshteinSearchParams(max_l_dist, max_l_dist,
                                                max_l_dist, max_l_dist)
        return consolidate_overlapping_matches(
            fnm_generic_ngrams(subsequence, sequence, search_params)
        )


class TestGenericSearchLpAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                             unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        search_params = LevenshteinSearchParams(max_subs, 0, 0, max_subs)
        return list(
            fnm_generic_lp(subsequence, sequence, search_params)
        )

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        return self.assertEqual(search_results, expected_outcomes, *args, **kwargs)


class TestGenericSearchNgramsAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                                 unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        if max_subs >= len(subsequence):
            self.skipTest("avoiding calling fnm_generic_ngrams() " +
                          "with max_subs >= len(subsequence)")
        search_params = LevenshteinSearchParams(max_subs, 0, 0, max_subs)
        return consolidate_overlapping_matches(
            fnm_generic_ngrams(subsequence, sequence, search_params)
        )

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


class TestGenericSearchBase(object):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        raise NotImplementedError

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.assertEqual(self.search(b('PATTERN'), b(''), 0, 0, 0, 0), [])

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search(b(''), b('TEXT'), 0, 0, 0, 0)

    def test_match_identical_sequence(self):
        self.assertEqual(
            self.search(b('PATTERN'), b('PATTERN'), 0, 0, 0, 0),
            [Match(start=0, end=7, dist=0, matched=b('PATTERN'))],
        )

    def test_short_substring(self):
        substring = b('XY')
        text = b('abcdefXYghij')
        expected_match = Match(start=6, end=8, dist=0, matched=substring)

        self.assertEqual(
            self.search(substring, text, 0, 0, 0, 0),
            [expected_match],
        )

    def test_substring(self):
        substring = b('PATTERN')
        text = b('aaaaaaaaaaPATTERNaaaaaaaaa')
        expected_match = Match(start=10, end=17, dist=0, matched=substring)

        self.assertEqual(
            self.search(substring, text, 0, 0, 0, 0),
            [expected_match],
        )

    def test_substring_in_long_text(self):
        substring = b('PATTERN')
        text = b(''.join([x.strip() for x in '''\
            FySijRLMtLLWkMnWxTbzIWuxOUbfAahWYKUlOZyhoQhfExJPOSwXxBLrlqdoUwpRW
            FEtHFiepnOTbkttuagADQaUTvkvKzvqaFaMnAPfolPpmXitKLDQhAqDOJwFzdcKmk
            cfVStxZGDUbrHjrDwVVRihbklyfqLJjrzGuhVGDzgSpCHXvaGPHebbcUAnAgfqqpA
            uMOowtptcoQUeAbdqJAmieLDxCrOPivbSwmriQwfFCDTXbswFqClZPnSkDkCyvPCi
            bmAjVGnuVsrZlPypglXlVVQKzMpQuWQynOLGDqwrAnsvYTcArkEhFpEgahWVQGOvv
            CTvbYZRVqqPCDRsyWeTVgANxZIyVAtENnndbsHzpEcPUfqCBUroIGRNEIMHYIZANy
            LeeVKEwihbvWZVOWPeAlmNKnhhoEPIcpDJDzPOYHSltxhSsZeeWMqtAnuSoFOIrqB
            EPUFIlKkpamljHylnTIWqaESoWbYESVPEeZtlAzpInuwFaNIYUvzpJNIlPtuOjUuT
            efaGnOXvQeHdaRPrdHCepPATTERNDdnkzuLHQcVWKpgHhGifBySAkWkthrzfZDHDU
            HJxjpLXseKuldLRftyctGvVKyrRTUCRAakjwTSWivGdksOZabnkBoRtMstlNwXcwg
            UCFLaWFxjqjasOfNeThrbubVGtyYRROYUOTMUmeSdJcBKxVXiaWDZoHyKtQRXwpVO
            pEmlpdzKWkFpDtHHdImhDJIXwxzjwyNLaTgPLHmcyhJGqncCblxALMdPEDaRtGFMg
            BskUxPGATTLKMFeIjgFJpudyMWlASyFSiaDWrOCgRfwjfpMYfuNQIqzvZbguWsnaq
            tRaXcxavobetBbbfMDjstQLjoJLwiajVRKhFVspIdgrmTMEBbjtpMnSpTkmFcRBZZ
            GUOWnesGgZeKkIQhlxlRPTtjUbbpaPlmxeiBdUKHHApgvEybUwWwXCoXFsauNiINm
            AGATFdcaHzgoRpbBFhKdJkLMF'''.splitlines()]))
        expected_match = Match(start=541, end=548, dist=0, matched=substring)

        self.assertEqual(
            self.search(substring, text, 0, 0, 0, 0),
            [expected_match],
        )

    def test_single_substitution_in_long_text(self):
        substring = b('PATTERN')
        text = b(''.join([x.strip() for x in '''\
            FySijRLMtLLWkMnWxTbzIWuxOUbfAahWYKUlOZyhoQhfExJPOSwXxBLrlqdoUwpRW
            FEtHFiepnOTbkttuagADQaUTvkvKzvqaFaMnAPfolPpmXitKLDQhAqDOJwFzdcKmk
            cfVStxZGDUbrHjrDwVVRihbklyfqLJjrzGuhVGDzgSpCHXvaGPHebbcUAnAgfqqpA
            uMOowtptcoQUeAbdqJAmieLDxCrOPivbSwmriQwfFCDTXbswFqClZPnSkDkCyvPCi
            bmAjVGnuVsrZlPypglXlVVQKzMpQuWQynOLGDqwrAnsvYTcArkEhFpEgahWVQGOvv
            CTvbYZRVqqPCDRsyWeTVgANxZIyVAtENnndbsHzpEcPUfqCBUroIGRNEIMHYIZANy
            LeeVKEwihbvWZVOWPeAlmNKnhhoEPIcpDJDzPOYHSltxhSsZeeWMqtAnuSoFOIrqB
            EPUFIlKkpamljHylnTIWqaESoWbYESVPEeZtlAzpInuwFaNIYUvzpJNIlPtuOjUuT
            efaGnOXvQeHdaRPrdHCepPATXERNDdnkzuLHQcVWKpgHhGifBySAkWkthrzfZDHDU
            HJxjpLXseKuldLRftyctGvVKyrRTUCRAakjwTSWivGdksOZabnkBoRtMstlNwXcwg
            UCFLaWFxjqjasOfNeThrbubVGtyYRROYUOTMUmeSdJcBKxVXiaWDZoHyKtQRXwpVO
            pEmlpdzKWkFpDtHHdImhDJIXwxzjwyNLaTgPLHmcyhJGqncCblxALMdPEDaRtGFMg
            BskUxPGATTLKMFeIjgFJpudyMWlASyFSiaDWrOCgRfwjfpMYfuNQIqzvZbguWsnaq
            tRaXcxavobetBbbfMDjstQLjoJLwiajVRKhFVspIdgrmTMEBbjtpMnSpTkmFcRBZZ
            GUOWnesGgZeKkIQhlxlRPTtjUbbpaPlmxeiBdUKHHApgvEybUwWwXCoXFsauNiINm
            AGATFdcaHzgoRpbBFhKdJkLMF'''.splitlines()]))
        expected_match = Match(start=541, end=548, dist=1,
                               matched=text[541:548])

        self.assertEqual(
            self.search(substring, text, 1, 0, 0, 1),
            [expected_match],
        )

        self.assertEqual(
            self.search(substring, text, 1, 1, 1, 1),
            [expected_match],
        )

    def test_double_first_item(self):
        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 0, 0, 0, 0),
            [Match(start=4, end=7, dist=0, matched=b('def'))],
        )

        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 1, 0, 0, 1),
            [Match(start=4, end=7, dist=0, matched=b('def'))],
        )

        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 0, 0, 1, 1),
            [Match(start=4, end=7, dist=0, matched=b('def')),
             Match(start=5, end=7, dist=1, matched=b('ef'))]
        )

        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 0, 1, 0, 1),
            [Match(start=3, end=7, dist=1, matched=b('ddef')),
             Match(start=4, end=7, dist=0, matched=b('def'))],
        )

    def test_missing_second_item(self):
        self.assertEqual(
            self.search(b('bde'), b('abcdefg'), 0, 1, 0, 1),
            [Match(start=1, end=5, dist=1, matched=b('bcde'))],
        )

        self.assertEqual(
            self.search(b('bde'), b('abcdefg'), 0, 0, 0, 0),
            [],
        )

        self.assertEqual(
            self.search(b('bde'), b('abcdefg'), 1, 0, 0, 1),
            [Match(start=2, end=5, dist=1, matched=b('cde'))],
        )

        self.assertEqual(
            self.search(b('bde'), b('abcdefg'), 0, 0, 1, 1),
            [Match(start=3, end=5, dist=1, matched=b('de'))],
        )

    def test_null_bytes(self):
        self.assertEqual(
            self.search(b('abc'), b('xx\0abcxx'), 0, 0, 0, 0),
            [Match(start=3, end=6, dist=0, matched=b('abc'))],
        )

        self.assertEqual(
            self.search(b('a\0b'), b('xxa\0bcxx'), 0, 0, 0, 0),
            [Match(start=2, end=5, dist=0, matched=b('a\0b'))],
        )

    def test_valid_none_arguments_with_defined_max_l_dist(self):
        # expect no exception when max_l_dist is not None and some or all other
        # values are None
        N = None
        for (max_subs, max_ins, max_dels) in [
            (N, 0, 0),
            (0, N, 0),
            (0, 0, N),
            (0, N, N),
            (N, 0, N),
            (N, N, 0),
            (N, N, N),
        ]:
            with self.subTest('max_subs={0}, max_ins={1}, max_dels={2}, max_l_dist=0'.format(
                    max_subs, max_ins, max_dels)):
                self.assertEqual(
                    self.search(b('a'), b('b'), max_subs, max_ins, max_dels, 0),
                    [],
                )

    def test_only_max_l_dist_none(self):
        # expect no exception when only max_l_dist is None
        self.assertEqual(
            self.search(b('a'), b('b'), 0, 0, 0, None),
            [],
        )

    def test_no_deletion(self):
        self.assertEqual(
            self.search(b('PATTERN'), b('---PATERN---'), None, None, 0, 1),
            []
        )

    def test_only_deletions(self):
        self.expectedOutcomes(
            self.search(b('TESTabc'), b('TEST123'), 0, 0, 5, None),
            [
                Match(start=0, end=4, dist=3, matched=b('TEST')),
                Match(start=1, end=4, dist=4, matched=b('EST')),
                Match(start=2, end=4, dist=5, matched=b('ST')),
            ],
        )

    def test_invalid_none_arguments(self):
        # check that an exception is raised when max_l_dist is None as well as
        # at least one other limitation
        N = None
        for (max_subs, max_ins, max_dels) in [
            (N, 0, 0),
            (0, N, 0),
            (0, 0, N),
            (0, N, N),
            (N, 0, N),
            (N, N, 0),
            (N, N, N),
        ]:
            with self.subTest('max_subs={0}, max_ins={1}, max_dels={2}, max_l_dist=None'.format(
                    max_subs, max_ins, max_dels)):
                with self.assertRaises(ValueError):
                    self.search(b('a'), b('b'), max_subs, max_ins, max_dels, None)


class TestGenericSearch(TestGenericSearchBase, unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        search_params = LevenshteinSearchParams(max_subs, max_ins,
                                                max_dels, max_l_dist)
        return consolidate_overlapping_matches(
            find_near_matches_generic(pattern, sequence, search_params)
        )

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        consolidated_expected_outcomes = \
            consolidate_overlapping_matches(expected_outcomes)
        return self.assertEqual(search_results, consolidated_expected_outcomes)

    def test_non_string_sequences(self):
        supported_types = [list, tuple]
        for klass in supported_types:
            with self.subTest(klass.__name__):
                self.expectedOutcomes(self.search(klass([1, 2, 3]), klass([1, 2, 3]), 0, 0, 0, 0),
                                      [Match(start=0, end=3, dist=0,
                                             matched=klass([1, 2, 3]))])
                self.expectedOutcomes(self.search(klass([1, 2, 3]), klass([1, 2, 3]), 1, 1, 1, 1),
                                      [Match(start=0, end=3, dist=0,
                                             matched=klass([1, 2, 3]))])
                self.expectedOutcomes(self.search(klass([1, 2, 3]), klass([1, 2, 4]), 0, 0, 0, 0),
                                      [])
                self.expectedOutcomes(self.search(klass([1, 2, 3]), klass([1, 2, 4]), 1, 1, 1, 1),
                                      [Match(start=0, end=3, dist=1,
                                             matched=klass([1, 2, 4]))])
                self.expectedOutcomes(self.search(klass([1, 2, 3]), klass([1, 2, 4]), 0, 0, 1, 1),
                                      [Match(start=0, end=2, dist=1,
                                             matched=klass([1, 2]))])

    def test_list_of_words_one_missing(self):
        subsequence = "jumped over the a lazy dog".split()
        sequence = "the big brown fox jumped over the lazy dog".split()
        for params, expected_outcomes in [
            ((0, 0, 0, 0), []),
            ((1, 0, 0, 1), []),
            ((0, 1, 0, 1), []),
            ((0, 0, 1, 1), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
            ((1, 1, 1, 1), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
            ((2, 2, 2, 2), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
        ]:
            self.expectedOutcomes(
                self.search(subsequence, sequence, *params),
                expected_outcomes,
            )

    def test_list_of_words_one_extra(self):
        subsequence = "jumped over lazy dog".split()
        sequence = "the big brown fox jumped over the lazy dog".split()
        for params, expected_outcomes in [
            ((0, 0, 0, 0), []),
            ((1, 0, 0, 1), []),
            ((0, 1, 0, 1), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
            ((0, 0, 1, 1), []),
            ((1, 1, 1, 1), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
            ((2, 2, 2, 2), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
        ]:
            self.expectedOutcomes(
                self.search(subsequence, sequence, *params),
                expected_outcomes,
            )

    def test_list_of_words_one_substituted(self):
        subsequence = "jumped over my lazy dog".split()
        sequence = "the big brown fox jumped over the lazy dog".split()
        for params, expected_outcomes in [
            ((0, 0, 0, 0), []),
            ((1, 0, 0, 1), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
            ((0, 1, 0, 1), []),
            ((0, 0, 1, 1), []),
            # substitution = insertion + deletion; dist = 1 !!
            ((0, 1, 1, 1), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
            ((1, 1, 1, 1), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
            ((2, 2, 2, 2), [Match(start=4, end=9, dist=1,
                                  matched="jumped over the lazy dog".split())]),
        ]:
            self.expectedOutcomes(
                self.search(subsequence, sequence, *params),
                expected_outcomes,
            )


class TestNgramsBase(object):
    def test_subseq_length_less_than_max_l_dist(self):
        with self.assertRaises(ValueError):
            self.search(b('b'), b('abc'), 2, 2, 2, 2)

        with self.assertRaises(ValueError):
            self.search(b('b'), b('abc'), 5, 5, 5, 5)

        with self.assertRaises(ValueError):
            self.search(b('PATTERN'), b('PATTERN'),
                        len('PATTERN') + 1,
                        len('PATTERN') + 1,
                        len('PATTERN') + 1,
                        len('PATTERN') + 1,
                        )

        with self.assertRaises(ValueError):
            self.search(b('PATTERN'), b('PATTERN'),
                        len('PATTERN') + 7,
                        len('PATTERN') + 7,
                        len('PATTERN') + 7,
                        len('PATTERN') + 7,
                        )


class TestGenericSearchLp(TestGenericSearchBase, unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        search_params = LevenshteinSearchParams(max_subs, max_ins,
                                                max_dels, max_l_dist)
        return list(
            fnm_generic_lp(pattern, sequence, search_params)
        )

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        self.assertEqual(search_results, expected_outcomes, *args, **kwargs)

    def test_double_first_item_two_results(self):
        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 0, 1, 0, 1),
            [Match(start=3, end=7, dist=1, matched=b('ddef')),
             Match(start=4, end=7, dist=0, matched=b('def'))],
        )

    def test_missing_second_item_complex(self):
        self.expectedOutcomes(
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


class TestGenericSearchNgrams(TestGenericSearchBase,
                              TestNgramsBase,
                              unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels, max_l_dist=None):
        search_params = LevenshteinSearchParams(max_subs, max_ins,
                                                max_dels, max_l_dist)
        return consolidate_overlapping_matches(
            fnm_generic_ngrams(pattern, sequence, search_params)
        )

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        consolidated_results = [
            get_best_match_in_group(group)
            for group in group_matches(search_results)
        ]
        consolidated_expected_outcomes = \
            consolidate_overlapping_matches(expected_outcomes)
        return self.assertEqual(consolidated_results,
                                consolidated_expected_outcomes,
                                *args, **kwargs)

    def test_missing_second_item_complex(self):
        self.assertTrue(
            set(self.search(b('bde'), b('abcdefg'), 1, 1, 1, 1)).issubset([
                Match(start=1, end=5, dist=1, matched=b('bcde')),
                Match(start=2, end=5, dist=1, matched=b('cde')),
                Match(start=3, end=5, dist=1, matched=b('de')),
            ])
        )


class TestHasNearMatchGenericNgramsAsSubstitutionsOnly(
    TestHasNearMatchSubstitionsOnlyBase,
):
    def search(self, subsequence, sequence, max_subs):
        return hnm_generic_ngrams(subsequence, sequence,
                                  LevenshteinSearchParams(max_subs, 0, 0, max_subs))


class TestHasNearMatchGenericNgrams(TestGenericSearchBase,
                                    TestNgramsBase,
                                    unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        return hnm_generic_ngrams(pattern, sequence,
                                  LevenshteinSearchParams(max_subs, max_ins, max_dels, max_l_dist))

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kwargs):
        self.assertEqual(bool(search_results),
                         bool(expected_outcomes),
                         *args, **kwargs)

    def assertEqual(self, actual_value, expected_value, *args, **kwargs):
        return super(TestHasNearMatchGenericNgrams, self).assertEqual(
            actual_value, bool(expected_value), *args, **kwargs)

    def test_missing_second_item_complex(self):
        self.assertTrue(self.search(b('bde'), b('abcdefg'), 1, 1, 1, 1))
