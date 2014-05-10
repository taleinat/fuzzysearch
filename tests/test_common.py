from fuzzysearch.common import Match, group_matches, GroupOfMatches, \
    search_exact, _count_differences_with_maximum
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
    def search(self, sequence, subsequence):
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


class TestSearchExact(TestSearchExactBase, unittest.TestCase):
    def search(self, sequence, subsequence):
        return list(search_exact(sequence, subsequence))

    def test_bytes(self):
        text = b('abc')
        self.assertEqual(self.search(text, text), [0])

    def test_unicode_identical(self):
        text = u('abc')
        self.assertEqual(self.search(text, text), [0])

    def test_unicode_substring(self):
        pattern = u('\u03A3\u0393')
        text = u('\u03A0\u03A3\u0393\u0394')
        self.assertEqual(self.search(pattern, text), [1])

    def test_biopython_Seq(self):
        try:
            from Bio.Seq import Seq
        except ImportError:
            raise unittest.SkipTest('Test requires BioPython')
        else:
            self.assertEqual(self.search(Seq('abc'), Seq('abc')), [0])


class TestCountDifferencesWithMaximumBase(object):
    def count_diffs(self, seq1, seq2, max_diffs):
        raise NotImplementedError

    def test_empty(self):
        result = self.count_diffs(b'', b'', 1)
        self.assertEqual(result, 0)

    def test_identical_one_character(self):
        result = self.count_diffs(b'a', b'a', 1)
        self.assertEqual(result, 0)

    def test_identical_word(self):
        result = self.count_diffs(b'word', b'word', 1)
        self.assertEqual(result, 0)

    def test_identical_long(self):
        result = self.count_diffs(b'long'*10, b'long'*10, 1)
        self.assertEqual(result, 0)

    def test_different_less_than_max(self):
        result = self.count_diffs(b'abc', b'def', 4)
        self.assertEqual(result, 3)

    def test_different_more_than_max(self):
        result = self.count_diffs(b'abc', b'def', 2)
        self.assertEqual(result, 2)

    def test_partially_different_in_middle(self):
        result = self.count_diffs(b'abcdef', b'a--d-f', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs(b'abcdef', b'a--d-f', 2)
        self.assertEqual(result, 2)

    def test_partially_different_at_start(self):
        result = self.count_diffs(b'abcdef', b'--c-ef', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs(b'abcdef', b'--c-ef', 2)
        self.assertEqual(result, 2)

    def test_partially_different_at_end(self):
        result = self.count_diffs(b'abcdef', b'ab-d--', 4)
        self.assertEqual(result, 3)

        result = self.count_diffs(b'abcdef', b'ab-d--', 2)
        self.assertEqual(result, 2)


class TestCountDifferencesWithMaximum(TestCountDifferencesWithMaximumBase,
                                      unittest.TestCase):
    def count_diffs(self, seq1, seq2, max_diffs):
        return _count_differences_with_maximum(seq1, seq2, max_diffs)


try:
    from fuzzysearch._common import count_differences_with_maximum_byteslike, \
        search_exact_byteslike
except ImportError:
    pass
else:
    class TestCountDifferencesWithMaximumByteslike(
        TestCountDifferencesWithMaximumBase, unittest.TestCase):
        def count_diffs(self, seq1, seq2, max_diffs):
            return count_differences_with_maximum_byteslike(seq1, seq2,
                                                            max_diffs)

    class TestSearchExactByteslike(TestSearchExactBase, unittest.TestCase):
        def search(self, sequence, subsequence):
            return search_exact_byteslike(sequence, subsequence)

        def test_bytes(self):
            text = b('abc')
            self.assertEqual(self.search(text, text), [0])
