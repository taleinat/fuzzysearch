from tests.compat import unittest, mock

from fuzzysearch import find_near_matches, Match


class MockFunctionFailsUnlessDefined(object):
    UNDEFINED = object()

    def __init__(self):
        self.return_value = self.UNDEFINED
        self.call_count = 0
        self.call_args = None

    def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args = (args, kwargs)

        if self.return_value is self.UNDEFINED:
            raise Exception('Undefined mock function called!')
        else:
            return self.return_value


class TestFindNearMatches(unittest.TestCase):
    def setUp(self):
        self.mock_search_exact = MockFunctionFailsUnlessDefined()
        self.mock_find_near_matches_levenshtein = \
            MockFunctionFailsUnlessDefined()
        self.mock_find_near_matches_substitutions = \
            MockFunctionFailsUnlessDefined()
        self.mock_find_near_matches_generic_linear_programming = \
            MockFunctionFailsUnlessDefined()

        patcher = mock.patch.multiple(
            'fuzzysearch',
            search_exact=self.mock_search_exact,
            find_near_matches_levenshtein=
                self.mock_find_near_matches_levenshtein,
            find_near_matches_substitutions=
                self.mock_find_near_matches_substitutions,
            find_near_matches_generic_linear_programming=
                self.mock_find_near_matches_generic_linear_programming,
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_no_limitations(self):
        with self.assertRaises(Exception):
            find_near_matches('a', 'a')

    def test_unlimited_parameter(self):
        with self.assertRaises(Exception):
            find_near_matches('a', 'a', max_substitutions=1)

        with self.assertRaises(Exception):
            find_near_matches('a', 'a', max_insertions=1)

        with self.assertRaises(Exception):
            find_near_matches('a', 'a', max_deletions=1)

        with self.assertRaises(Exception):
            find_near_matches('a', 'a', max_substitutions=1, max_insertions=1)

        with self.assertRaises(Exception):
            find_near_matches('a', 'a', max_substitutions=1, max_deletions=1)

        with self.assertRaises(Exception):
            find_near_matches('a', 'a', max_insertions=1, max_deletions=1)

    def test_all_zero(self):
        self.mock_search_exact.return_value = [42]
        self.assertEqual(
            find_near_matches('a', 'a', 0, 0, 0, 0),
            [Match(42, 43, 0)],
        )
        self.assertEqual(self.mock_search_exact.call_count, 1)

    def test_zero_max_l_dist(self):
        self.mock_search_exact.return_value = [42]

        call_count = 0
        for (max_subs, max_ins, max_dels) in [
            (1, 0, 0),
            (0, 1, 0),
            (1, 0, 1),
            (1, 1, 0),
            (1, 0, 1),
            (0, 1, 1),
            (1, 1, 1),
        ]:
            self.assertEqual(
                find_near_matches('a', 'a', max_subs, max_ins, max_dels, 0),
                [Match(42, 43, 0)],
            )
            call_count += 1
            msg = 'failed with max_subs={}, max_ins={}, max_dels={}'.format(
                max_subs, max_ins, max_dels,
            )
            self.assertEqual(self.mock_search_exact.call_count, call_count, msg)

    def test_all_zero_except_max_l_dist(self):
        self.mock_search_exact.return_value = [42]

        self.assertEqual(
            find_near_matches('a', 'a', 0, 0, 0, 1),
            [Match(42, 43, 0)],
        )
        self.assertEqual(self.mock_search_exact.call_count, 1)

    def test_levenshtein(self):
        """test cases where 0 < max_l_dist <= max(others)"""
        # in these cases, find_near_matches should call
        # find_near_matches_levenshtein
        self.mock_find_near_matches_levenshtein.return_value = \
            [mock.sentinel.SENTINEL]

        self.assertEqual(
            find_near_matches('a', 'a', 1, 1, 1, 1),
            [mock.sentinel.SENTINEL],
        )
        self.assertEqual(self.mock_find_near_matches_levenshtein.call_count, 1)

        self.assertEqual(
            find_near_matches('a', 'a', 2, 2, 2, 2),
            [mock.sentinel.SENTINEL],
        )
        self.assertEqual(self.mock_find_near_matches_levenshtein.call_count, 2)

        self.assertEqual(
            find_near_matches('a', 'a', 5, 3, 7, 2),
            [mock.sentinel.SENTINEL],
        )
        self.assertEqual(self.mock_find_near_matches_levenshtein.call_count, 3)

    def test_only_substitutions(self):
        self.mock_find_near_matches_substitutions.return_value = [42]

        self.assertEqual(
            find_near_matches('a', 'a', 1, 0, 0),
            [42],
        )
        self.assertEqual(
            self.mock_find_near_matches_substitutions.call_count,
            1,
        )

        self.assertEqual(
            find_near_matches('a', 'a', 1, 0, 0, 1),
            [42],
        )
        self.assertEqual(
            self.mock_find_near_matches_substitutions.call_count,
            2,
        )

    def test_generic(self):
        self.mock_find_near_matches_generic_linear_programming.return_value = [42]

        self.assertEqual(
            find_near_matches('a', 'a', 1, 1, 1),
            [42],
        )
        self.assertEqual(
            self.mock_find_near_matches_generic_linear_programming.call_count,
            1,
        )

        self.assertEqual(
            find_near_matches('a', 'a', 1, 1, 1, 2),
            [42],
        )
        self.assertEqual(
            self.mock_find_near_matches_generic_linear_programming.call_count,
            2,
        )
