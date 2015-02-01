from fuzzysearch.common import group_matches, Match, get_best_match_in_group, \
    count_differences_with_maximum
from fuzzysearch.substitutions_only import \
    has_near_match_substitutions as hnm_subs, \
    find_near_matches_substitutions as fnm_subs, \
    find_near_matches_substitutions_lp as fnm_subs_lp, \
    has_near_match_substitutions_lp as hnm_subs_lp, \
    find_near_matches_substitutions_ngrams as fnm_subs_ngrams, \
    has_near_match_substitutions_ngrams as hnm_subs_ngrams

from tests.compat import unittest

from six import b


class TestSubstitionsOnlyBase(object):
    def search(self, subsequence, sequence, max_subs):
        raise NotImplementedError

    def expectedOutcomes(self, search_result, expected_outcomes):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.expectedOutcomes(self.search('PATTERN', '', max_subs=0), [])

    def test_empty_subsequence_exeption(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT', max_subs=0)

    def test_match_identical_sequence(self):
        self.expectedOutcomes(
            self.search('PATTERN', 'PATTERN', max_subs=0),
            [Match(start=0, end=len('PATTERN'), dist=0)],
        )

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=0)

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
            self.search('def', 'abcddefg', max_subs=1),
            [Match(start=4, end=7, dist=0)],
        )

        self.expectedOutcomes(
            self.search('def', 'abcddefg', max_subs=2),
            [Match(start=3, end=6, dist=2),
             Match(start=4, end=7, dist=0)],
        )

    def test_two_identical(self):
        self.expectedOutcomes(
            self.search('abc', 'abcabc', max_subs=1),
            [Match(start=0, end=3, dist=0), Match(start=3, end=6, dist=0)],
        )

        self.expectedOutcomes(
            self.search('abc', 'abcXabc', max_subs=1),
            [Match(start=0, end=3, dist=0), Match(start=4, end=7, dist=0)],
        )

    def test_one_changed_in_middle(self):
        substring = 'abcdefg'
        pattern = 'abcXefg'
        expected_match = Match(start=0, end=7, dist=1)

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
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATERNaaaaaaaaa'

        for max_subs in [0, 1, 2]:
            self.expectedOutcomes(
                self.search(substring, text, max_subs=max_subs),
                [],
            )

    def test_one_changed_in_middle2(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATtERNaaaaaaaaa'
        expected_match = Match(start=10, end=17, dist=1)

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
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTXERNaaaaaaaaa'

        for max_subs in [0, 1, 2]:
            self.expectedOutcomes(
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

        self.expectedOutcomes(
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

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=0),
            [Match(start=42, end=52, dist=0),
             Match(start=99, end=109, dist=0)],
        )

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=1),
            [Match(start=19, end=29, dist=1),
             Match(start=42, end=52, dist=0),
             Match(start=99, end=109, dist=0)],
        )

        self.expectedOutcomes(
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

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=0),
            [Match(start=99, end=109, dist=0)],
        )

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=1),
            [Match(start=19, end=29, dist=1),
             Match(start=42, end=52, dist=1),
             Match(start=99, end=109, dist=0)],
        )

        self.expectedOutcomes(
            self.search(pattern, text, max_subs=2),
            [Match(start=19, end=29, dist=1),
             Match(start=42, end=52, dist=1),
             Match(start=99, end=109, dist=0)],
        )

    def test_missing_at_beginning(self):
        self.expectedOutcomes(
            self.search("ATTEST", "TESTOSTERONE", max_subs=2),
            [],
        )


class TestFindNearMatchesSubstitions(TestSubstitionsOnlyBase,
                                     unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return fnm_subs(subsequence, sequence, max_subs)

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


class TestFindNearMatchesSubstitionsLinearProgramming(TestSubstitionsOnlyBase,
                                                      unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return list(fnm_subs_lp(subsequence, sequence, max_subs))

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kw):
        return self.assertEqual(search_results, expected_outcomes, *args, **kw)


class TestFindNearMatchesSubstitionsNgrams(TestSubstitionsOnlyBase,
                                           unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return fnm_subs_ngrams(subsequence, sequence, max_subs)

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



class TestHasNearMatchSubstitionsOnlyBase(TestSubstitionsOnlyBase):
    def search(self, subsequence, sequence, max_subs):
        raise NotImplementedError

    def expectedOutcomes(self, search_results, expected_outcomes, *args, **kw):
        return self.assertEqual(bool(search_results),
                                bool(expected_outcomes),
                                *args, **kw)


class TestHasNearMatchSubstitionsOnly(TestHasNearMatchSubstitionsOnlyBase,
                                      unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
        return hnm_subs(subsequence, sequence, max_subs)


class TestHasNearMatchSubstitionsOnlyNgrams(TestHasNearMatchSubstitionsOnlyBase,
                                            unittest.TestCase):
    def search(self, subsequence, sequence, max_subs):
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
        def search(self, subsequence, sequence, max_subs):
            return hnm_subs_lp_byteslike(b(subsequence), b(sequence),
                                         max_subs)

    class TestHasNearMatchesSubstitionsNgramsByteslike(
            TestHasNearMatchSubstitionsOnlyBase,
            unittest.TestCase
    ):
        def search(self, subsequence, sequence, max_subs):
            return hnm_subs_ngrams_byteslike(b(subsequence), b(sequence),
                                             max_subs)

    class TestFindNearMatchesSubstitionsLpByteslike(
            TestSubstitionsOnlyBase,
            unittest.TestCase
    ):
        def search(self, subsequence, sequence, max_subs):
            results = fnm_subs_lp_byteslike(b(subsequence), b(sequence),
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
                )
                for index in results
            ]
            return matches

        def expectedOutcomes(self, search_results, expected_outcomes,
                             *args, **kw):
            return self.assertEqual(search_results, expected_outcomes,
                                    *args, **kw)

    class TestFindNearMatchesSubstitionsNgramsByteslike(
            TestSubstitionsOnlyBase,
            unittest.TestCase
    ):
        def search(self, subsequence, sequence, max_subs):
            results = fnm_subs_ngrams_byteslike(b(subsequence), b(sequence),
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
                )
                for index in results
            ]
            return [
                get_best_match_in_group(group)
                for group in group_matches(matches)
            ]

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
