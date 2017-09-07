from fuzzysearch.common import Match, group_matches, GroupOfMatches, \
    search_exact, count_differences_with_maximum
from tests.compat import unittest

from six import b, u


class TestGroupOfMatches(unittest.TestCase):
    def test_is_match_in_group(self):
        match = Match(2, 4, 0)
        group = GroupOfMatches(match)
        self.assertTrue(group.is_match_in_group(match))
        self.assertTrue(group.is_match_in_group(Match(2, 4, 0)))


class TestGroupMatches(unittest.TestCase):
    def test_separate(self):
        matches = [
            Match(start=19, end=29, dist=1),
            Match(start=42, end=52, dist=1),
            Match(start=99, end=109, dist=0),
        ]
        self.assertEqual(
            group_matches(matches),
            [set([m]) for m in matches],
        )

    def test_separate_with_duplicate(self):
        matches = [
            Match(start=19, end=29, dist=1),
            Match(start=42, end=52, dist=1),
            Match(start=99, end=109, dist=0),
        ]
        self.assertEqual(
            group_matches(matches + [matches[1]]),
            [set([m]) for m in matches],
        )


class TestSearchExactBase(object):
    def search(self, sequence, subsequence, start_index=0, end_index=None):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.assertEqual(self.search('PATTERN', ''), [])

    def test_empty_subsequence(self):
        with self.assertRaises(ValueError):
            self.search('', 'TEXT')

    def test_match_identical_sequence(self):
        self.assertEqual(self.search('PATTERN', 'PATTERN'), [0])

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        self.assertEqual(self.search(substring, text), [10])

    def test_double_first_item(self):
        self.assertEqual(self.search('def', 'abcddefg'), [4])

    def test_missing_second_item(self):
        self.assertEqual(self.search('bde', 'abcdefg'), [])

    def test_completely_different(self):
        self.assertEqual(self.search('abc', 'def'), [])

    def test_startswith(self):
        self.assertEqual(self.search('abc', 'abcd'), [0])

    def test_endswith(self):
        self.assertEqual(self.search('bcd', 'abcd'), [1])

    def get_supported_sequence_types(self):
        raise NotImplementedError

    def test_identical(self):
        # search for a pattern in itself, should match once at index 0
        for initializer in self.get_supported_sequence_types():
            pattern = initializer('abc')
            with self.subTest("search_exact({0!r}, {0!r})".format(pattern)):
                self.assertEqual(self.search(pattern, pattern), [0])

    def test_subsequence(self):
        # search for a pattern appearing once at index 4
        for initializer in self.get_supported_sequence_types():
            pattern = initializer('abc')
            sequence = initializer('-ab-abc-ab-')
            with self.subTest("search_exact({0!r}, {1!r})".format(pattern, sequence)):
                self.assertEqual(self.search(pattern, sequence), [4])

    def test_multiple_matches(self):
        # search for a pattern appearing at indexes 1, 5 and 9
        for initializer in self.get_supported_sequence_types():
            pattern = initializer('abc')
            sequence = initializer('-abc-abc-abc-')
            with self.subTest("search_exact({0!r}, {1!r})".format(pattern, sequence)):
                self.assertEqual(self.search(pattern, sequence), [1, 5, 9])

    def test_outside_range_limits(self):
        for initializer in self.get_supported_sequence_types():
            pattern = initializer('abc')
            sequence = initializer('-abc-abc-abc')
            with self.subTest("search_exact({0!r}, {1!r}, {2}, {3})".format(pattern, sequence, 0, 3)):
                self.assertEqual(self.search(pattern, sequence, 0, 3), [])
            with self.subTest("search_exact({0!r}, {1!r}, {2}, {3})".format(pattern, sequence, 0, 4)):
                self.assertEqual(self.search(pattern, sequence, 0, 4), [1])
            with self.subTest("search_exact({0!r}, {1!r}, {2}, {3})".format(pattern, sequence, 0, 7)):
                self.assertEqual(self.search(pattern, sequence, 0, 7), [1])
            with self.subTest("search_exact({0!r}, {1!r}, {2}, {3})".format(pattern, sequence, 0, 8)):
                self.assertEqual(self.search(pattern, sequence, 0, 8), [1, 5])
            with self.subTest("search_exact({0!r}, {1!r}, {2}, {3})".format(pattern, sequence, 0, 11)):
                self.assertEqual(self.search(pattern, sequence, 0, 11), [1, 5])
            with self.subTest("search_exact({0!r}, {1!r}, {2}, {3})".format(pattern, sequence, 0, 12)):
                self.assertEqual(self.search(pattern, sequence, 0, 12), [1, 5, 9])

            with self.subTest("search_exact({0!r}, {1!r}, {2})".format(pattern, sequence, 1)):
                self.assertEqual(self.search(pattern, sequence, 1), [1, 5, 9])
            with self.subTest("search_exact({0!r}, {1!r}, {2})".format(pattern, sequence, 2)):
                self.assertEqual(self.search(pattern, sequence, 2), [5, 9])
            with self.subTest("search_exact({0!r}, {1!r}, {2})".format(pattern, sequence, 5)):
                self.assertEqual(self.search(pattern, sequence, 5), [5, 9])
            with self.subTest("search_exact({0!r}, {1!r}, {2})".format(pattern, sequence, 6)):
                self.assertEqual(self.search(pattern, sequence, 6), [9])

            with self.subTest("search_exact({0!r}, {1!r}, {2}, {3})".format(pattern, sequence, 4, 10)):
                self.assertEqual(self.search(pattern, sequence, 4, 10), [5])

            with self.subTest("search_exact({0!r}, {1!r}, {2}, {3})".format(pattern, sequence, 3, 7)):
                self.assertEqual(self.search(pattern, sequence, 3, 7), [])

class TestSearchExact(TestSearchExactBase, unittest.TestCase):
    def search(self, sequence, subsequence, start_index=0, end_index=None):
        return list(search_exact(sequence, subsequence, start_index, end_index))

    def get_supported_sequence_types(self):
        types_to_test = [b, u, list, tuple]

        try:
            from Bio.Seq import Seq
            from Bio.Alphabet import IUPAC
        except ImportError:
            pass
        else:
            types_to_test.append(Seq)
            types_to_test.append(
                lambda text: Seq(text.replace('b', 'g').replace('-', 't'),
                                 alphabet=IUPAC.unambiguous_dna))

        return types_to_test

    def test_unicode_subsequence(self):
        self.assertEqual(self.search(u('\u03A3\u0393'), u('\u03A0\u03A3\u0393\u0394')), [1])


class TestCountDifferencesWithMaximumBase(object):
    def count_diffs(self, seq1, seq2, max_diffs):
        raise NotImplementedError

    def test_empty(self):
        result = self.count_diffs('', '', 1)
        self.assertEqual(result, 0)

    def test_identical_one_character(self):
        result = self.count_diffs('a', 'a', 1)
        self.assertEqual(result, 0)

    def test_identical_word(self):
        result = self.count_diffs('word', 'word', 1)
        self.assertEqual(result, 0)

    def test_identical_long(self):
        result = self.count_diffs('long'*10, 'long'*10, 1)
        self.assertEqual(result, 0)

    def test_different_less_than_max(self):
        result = self.count_diffs('abc', 'def', 4)
        self.assertEqual(result, 3)

    def test_different_more_than_max(self):
        result = self.count_diffs('abc', 'def', 2)
        self.assertEqual(result, 2)

    def test_partially_different_in_middle(self):
        result = self.count_diffs('abcdef', 'a--d-f', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs('abcdef', 'a--d-f', 2)
        self.assertEqual(result, 2)

    def test_partially_different_at_start(self):
        result = self.count_diffs('abcdef', '--c-ef', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs('abcdef', '--c-ef', 2)
        self.assertEqual(result, 2)

    def test_partially_different_at_end(self):
        result = self.count_diffs('abcdef', 'ab-d--', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs('abcdef', 'ab-d--', 2)
        self.assertEqual(result, 2)


class TestCountDifferencesWithMaximum(TestCountDifferencesWithMaximumBase,
                                      unittest.TestCase):
    def count_diffs(self, seq1, seq2, max_diffs):
        return count_differences_with_maximum(seq1, seq2, max_diffs)


try:
    from fuzzysearch._common import count_differences_with_maximum_byteslike, \
        search_exact_byteslike
except ImportError:
    pass
else:
    class TestCountDifferencesWithMaximumByteslike(
            TestCountDifferencesWithMaximumBase, unittest.TestCase):
        def count_diffs(self, seq1, seq2, max_diffs):
            return count_differences_with_maximum_byteslike(b(seq1), b(seq2),
                                                            max_diffs)

    class TestSearchExactByteslike(TestSearchExactBase, unittest.TestCase):
        def search(self, sequence, subsequence, start_index=0, end_index=None):
            if end_index is not None:
                return search_exact_byteslike(b(sequence), b(subsequence), start_index, end_index)
            else:
                return search_exact_byteslike(b(sequence), b(subsequence), start_index)

        def get_supported_sequence_types(self):
            types_to_test = [b]
            return types_to_test

        def test_input_argument_handling(self):
            self.assertEqual(search_exact_byteslike(b'abc', b'abc'), [0])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', 0), [0])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', 1), [])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', 0, 3), [0])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', 0, end_index=3), [0])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', end_index=3, start_index=0), [0])
            self.assertEqual(search_exact_byteslike(subsequence=b'abc', sequence=b'abc',
                                                    start_index=0, end_index=3), [0])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', 0, 4), [0])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', 0, -1), [0])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', 0, 2), [])
            self.assertEqual(search_exact_byteslike(b'abc', b'abc', 2, 1), [])

            with self.assertRaises(Exception):
                search_exact_byteslike(b'abc', subsequence=b'abc')

            with self.assertRaises(Exception):
                search_exact_byteslike(b'abc', b'abc', 0, start_index=0)
