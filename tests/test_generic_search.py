from tests.compat import unittest
from tests.test_levenshtein import TestFindNearMatchesLevenshteinBase
from fuzzysearch.common import Match, get_best_match_in_group, group_matches, LevenshteinSearchParams
from tests.test_substitutions_only import TestSubstitionsOnlyBase, \
    TestHasNearMatchSubstitionsOnly
from fuzzysearch.generic_search import \
    _find_near_matches_generic_linear_programming as fnm_generic_lp, \
    find_near_matches_generic_ngrams as fnm_generic_ngrams, \
    has_near_match_generic_ngrams as hnm_generic_ngrams, \
    find_near_matches_generic

from six import b


class TestGenericSearchLpAsLevenshtein(TestFindNearMatchesLevenshteinBase,
                                       unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return [
            get_best_match_in_group(group)
            for group in group_matches(
                fnm_generic_lp(subsequence, sequence,
                               LevenshteinSearchParams(max_l_dist, max_l_dist, max_l_dist, max_l_dist))
            )
        ]


class TestGenericSearchNgramsAsLevenshtein(TestFindNearMatchesLevenshteinBase,
                                       unittest.TestCase):
    def search(self, subsequence, sequence, max_l_dist):
        return fnm_generic_ngrams(subsequence, sequence,
                                  LevenshteinSearchParams(max_l_dist, max_l_dist, max_l_dist, max_l_dist))


class TestGenericSearchLpAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                             unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return list(
            fnm_generic_lp(subsequence, sequence, LevenshteinSearchParams(max_subs, 0, 0, max_subs))
        )

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kw):
        return self.assertEqual(search_results, expected_outcomes, *args, **kw)


class TestGenericSearchNgramsAsSubstitutionsOnly(TestSubstitionsOnlyBase,
                                             unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return fnm_generic_ngrams(subsequence, sequence,
                                  LevenshteinSearchParams(max_subs, 0, 0, max_subs))

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kw):
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
                                *args, **kw)


class TestGenericSearchBase(object):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        raise NotImplementedError

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kw):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.assertEqual(self.search(b('PATTERN'), b(''), 0, 0, 0, 0), [])

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search(b(''), b('TEXT'), 0, 0, 0, 0)

    def test_match_identical_sequence(self):
        self.assertEqual(
            self.search(b('PATTERN'), b('PATTERN'), 0, 0, 0, 0),
            [Match(start=0, end=7, dist=0)],
        )

    def test_short_substring(self):
        substring = b('XY')
        text = b('abcdefXYghij')
        expected_match = Match(start=6, end=8, dist=0)

        self.assertEqual(
            self.search(substring, text, 0, 0, 0, 0),
            [expected_match],
        )

    def test_substring(self):
        substring = b('PATTERN')
        text = b('aaaaaaaaaaPATTERNaaaaaaaaa')
        expected_match = Match(start=10, end=17, dist=0)

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
        expected_match = Match(start=541, end=548, dist=0)

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
        expected_match = Match(start=541, end=548, dist=1)

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
            [Match(start=4, end=7, dist=0)],
        )

        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 1, 0, 0, 1),
            [Match(start=4, end=7, dist=0)],
        )

        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 0, 0, 1, 1),
            [Match(start=4, end=7, dist=0),
             Match(start=5, end=7, dist=1)]
        )

        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 0, 1, 0, 1),
            [Match(start=3, end=7, dist=1),
             Match(start=4, end=7, dist=0)],
        )

    def test_missing_second_item(self):
        self.assertEqual(
            self.search(b('bde'), b('abcdefg'), 0, 1, 0, 1),
            [Match(start=1, end=5, dist=1)],
        )

        self.assertEqual(
            self.search(b('bde'), b('abcdefg'), 0, 0, 0, 0),
            [],
        )

        self.assertEqual(
            self.search(b('bde'), b('abcdefg'), 1, 0, 0, 1),
            [Match(start=2, end=5, dist=1)],
        )

        self.assertEqual(
            self.search(b('bde'), b('abcdefg'), 0, 0, 1, 1),
            [Match(start=3, end=5, dist=1)],
        )

    def test_null_bytes(self):
        self.assertEqual(
            self.search(b('abc'), b('xx\0abcxx'), 0, 0, 0, 0),
            [Match(start=3, end=6, dist=0)],
        )

        self.assertEqual(
            self.search(b('a\0b'), b('xxa\0bcxx'), 0, 0, 0, 0),
            [Match(start=2, end=5, dist=0)],
        )


class TestGenericSearch(TestGenericSearchBase, unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        return list(find_near_matches_generic(pattern, sequence,
                                              LevenshteinSearchParams(max_subs, max_ins, max_dels, max_l_dist)))

    def expectedOutcomes(self, search_results, expected_outcomes):
        best_from_grouped_exepected_outcomes = [
            get_best_match_in_group(group)
            for group in group_matches(expected_outcomes)
        ]
        return self.assertEqual(search_results,
                                best_from_grouped_exepected_outcomes)

    def test_valid_none_arguments(self):
        # check that no exception is raised when some values are None
        self.assertEqual(
            self.search(b('a'), b('b'), 0, None, None, 0),
            [],
        )

        self.assertEqual(
            self.search(b('a'), b('b'), None, 0, None, 0),
            [],
        )

        self.assertEqual(
            self.search(b('a'), b('b'), None, None, 0, 0),
            [],
        )

        self.assertEqual(
            self.search(b('a'), b('b'), 0, 0, None, 0),
            [],
        )

        self.assertEqual(
            self.search(b('a'), b('b'), 0, None, 0, 0),
            [],
        )

        self.assertEqual(
            self.search(b('a'), b('b'), None, 0, 0, 0),
            [],
        )

        self.assertEqual(
            self.search(b('a'), b('b'), None, None, None, 0),
            [],
        )

        self.assertEqual(
            self.search(b('a'), b('b'), 0, 0, 0, None),
            [],
        )

    def test_invalid_none_arguments(self):
        # check that an exception is raised when max_l_dist is None as well as
        # at least one other limitation
        with self.assertRaises(ValueError):
            self.search(b('a'), b('b'), None, None, None, None)


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
        return list(fnm_generic_lp(pattern, sequence,
                                   LevenshteinSearchParams(max_subs, max_ins, max_dels, max_l_dist)))

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kw):
        self.assertEqual(search_results, expected_outcomes, *args, **kw)

    def test_double_first_item_two_results(self):
        self.expectedOutcomes(
            self.search(b('def'), b('abcddefg'), 0, 1, 0, 1),
            [Match(start=3, end=7, dist=1),
             Match(start=4, end=7, dist=0)],
        )

    def test_missing_second_item_complex(self):
        self.expectedOutcomes(
            self.search(b('bde'), b('abcdefg'), 1, 1, 1, 1),
            [Match(start=1, end=5, dist=1),
             Match(start=2, end=5, dist=1),
             Match(start=3, end=5, dist=1)],
        )

        self.assertTrue(
            set([
                Match(start=1, end=5, dist=1),
                Match(start=2, end=5, dist=1),
                Match(start=3, end=5, dist=1),
                Match(start=2, end=5, dist=3),
            ]).issubset(set(
                self.search(b('bde'), b('abcdefg'), 1, 1, 1, 3),
            ))
        )

class TestGenericSearchNgrams(TestGenericSearchBase,
                              TestNgramsBase,
                              unittest.TestCase):
    def search(self, pattern, sequence, max_subs, max_ins, max_dels,
               max_l_dist=None):
        return fnm_generic_ngrams(pattern, sequence,
                                  LevenshteinSearchParams(max_subs, max_ins, max_dels, max_l_dist))

    def expectedOutcomes(self, search_results, expected_outcomes):
        best_from_grouped_results = [
            get_best_match_in_group(group)
            for group in group_matches(search_results)
        ]
        best_from_grouped_exepected_outcomes = [
            get_best_match_in_group(group)
            for group in group_matches(expected_outcomes)
        ]
        return self.assertEqual(best_from_grouped_results,
                                best_from_grouped_exepected_outcomes)

    def test_missing_second_item_complex(self):
        self.assertTrue(
            set(self.search(b('bde'), b('abcdefg'), 1, 1, 1, 1)).issubset([
                Match(start=1, end=5, dist=1),
                Match(start=2, end=5, dist=1),
                Match(start=3, end=5, dist=1),
            ])
        )


class TestHasNearMatchGenericNgramsAsSubstitutionsOnly(
    TestHasNearMatchSubstitionsOnly,
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

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kw):
        self.assertEqual(bool(search_results),
                         bool(expected_outcomes),
                         *args, **kw)

    def assertEqual(self, actual_value, expected_value, *args, **kw):
        return super(TestHasNearMatchGenericNgrams, self).assertEqual(
            actual_value, bool(expected_value), *args, **kw)

    def test_missing_second_item_complex(self):
        self.assertTrue(self.search(b('bde'), b('abcdefg'), 1, 1, 1, 1))
