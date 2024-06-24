import unittest

from tests.compat import b


class TestMemmemBase(object):
    def search(self, sequence, subsequence):
        raise NotImplementedError

    def test_empty_sequence(self):
        self.assertEqual(self.search('PATTERN', ''), None)

    def test_empty_subsequence(self):
        self.assertEqual(self.search('', 'TEXT'), 0)

    def test_match_identical_sequence(self):
        self.assertEqual(self.search('PATTERN', 'PATTERN'), 0)

    def test_shorter_sequence(self):
        self.assertEqual(self.search('abcd', 'abc'), None)

    def test_substring(self):
        substring = 'PATTERN'
        text = 'aaaaaaaaaaPATTERNaaaaaaaaa'
        self.assertEqual(self.search(substring, text), 10)

    def test_double_first_item(self):
        self.assertEqual(self.search('def', 'abcddefg'), 4)

    def test_missing_second_item(self):
        self.assertEqual(self.search('bde', 'abcdefg'), None)

    def test_completely_different(self):
        self.assertEqual(self.search('abc', 'def'), None)

    def test_startswith(self):
        self.assertEqual(self.search('abc', 'abcd'), 0)

    def test_endswith(self):
        self.assertEqual(self.search('bcd', 'abcd'), 1)

    def test_first_subseq_char_not_in_seq(self):
        self.assertEqual(self.search('xa', 'abcd'), None)

    def test_multiple_appearances(self):
        self.assertEqual(self.search('abc', 'xxxabcxxxabcxxxabcxxx'), 3)

    def test_single_letter_subseq(self):
        self.assertEqual(self.search('a', 'abc'), 0)
        self.assertEqual(self.search('b', 'abc'), 1)
        self.assertEqual(self.search('c', 'abc'), 2)
        self.assertEqual(self.search('a', 'xxx'), None)
        self.assertEqual(self.search('a', 'x'*100 + 'a' + 'x'*100), 100)
        self.assertEqual(self.search('a', ''), None)

    def test_subseq_lengths(self):
        import string
        letters = string.ascii_lowercase + string.ascii_uppercase
        for subseq_length in range(2, 100):
            subseq = letters[:subseq_length]
            self.assertEqual(self.search(subseq, letters), 0)
            self.assertEqual(self.search(subseq, 'a!'*50 + letters), 100)
            self.assertEqual(self.search(subseq, '!'*100), None)
            self.assertEqual(self.search(subseq, '!'), None)
            self.assertEqual(self.search(subseq, '!'*50 + 'a' + '!'*50), None)
            self.assertEqual(self.search(subseq, '!'*50 + 'a'), None)
            self.assertEqual(self.search(subseq, subseq[:-1]), None)
            self.assertEqual(self.search(subseq, subseq[:-1] * 2), None)
            self.assertEqual(self.search(subseq, subseq[:-1] + 'aa'), None)
            self.assertEqual(self.search(subseq, 'aa' + subseq[:-1]), None)
            self.assertEqual(self.search(subseq, 'aa' + subseq[:-1] + 'aa'), None)

try:
    from fuzzysearch._pymemmem import simple_memmem, wordlen_memmem
except ImportError:
    pass
else:
    class TestSimpleMemmem(TestMemmemBase, unittest.TestCase):
        def search(self, subsequence, sequence):
            return simple_memmem(b(subsequence), b(sequence))

    class TestWordlenMemmem(TestMemmemBase, unittest.TestCase):
        def search(self, subsequence, sequence):
            return wordlen_memmem(b(subsequence), b(sequence))
