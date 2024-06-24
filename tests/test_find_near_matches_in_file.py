import io
from itertools import product
import os
import re
import tempfile
import unittest
import unittest.mock

import attr

from fuzzysearch import find_near_matches_in_file
from fuzzysearch.common import Match

from tests.compat import b
import tests.test_find_near_matches


class TestSearchFile(unittest.TestCase):
    def test_file_openers(self):
        import codecs
        import io

        needle = 'PATTERN'
        haystack = '---PATERN---'

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            filename = f.name
            f.write(b(haystack))
        self.addCleanup(os.remove, filename)

        def test_file_bytes(f):
            self.assertEqual(find_near_matches_in_file(b(needle), f, max_l_dist=1),
                             [Match(3, 9, 1, b('PATERN'))])

        def test_file_unicode(f):
            self.assertEqual(find_near_matches_in_file(needle, f, max_l_dist=1),
                             [Match(3, 9, 1, 'PATERN')])

        with open(filename, 'rb') as f:
            test_file_bytes(f)

        with open(filename, 'r') as f:
            test_file_unicode(f)

        with codecs.open(filename, 'rb') as f:
            test_file_bytes(f)

        with codecs.open(filename, 'r') as f:
            test_file_unicode(f)

        with io.open(filename, 'rb') as f:
            test_file_bytes(f)

        with io.open(filename, 'r') as f:
            test_file_unicode(f)

    def test_unicode_encodings(self):
        needle = 'PATTERN'
        haystack = '---PATERN---'

        for encoding in ['ascii', 'latin-1', 'latin1', 'utf-8', 'utf-16']:
            with self.subTest(encoding=encoding):
                with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
                    filename = f.name
                    f.write(haystack.encode(encoding))
                self.addCleanup(os.remove, filename)
                with io.open(filename, 'r', encoding=encoding) as f:
                    self.assertEqual(
                        find_near_matches_in_file(needle, f, max_l_dist=1),
                        [Match(3, 9, 1, 'PATERN')],
                    )

    def test_subsequence_split_between_chunks(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            filename = f.name
        self.addCleanup(os.remove, filename)

        for needle, haystack_match, max_l_dist, expected_matches in [
            (b('PATTERN'), b('PATERN'), 0, []),
            (b('PATTERN'), b('PATERN'), 1, [Match(0, 6, 1, b('PATERN'))]),
            (b('PATTERN'), b('PATERN'), 2, [Match(0, 6, 1, b('PATERN'))]),
            (b('PATTERN'), b('PATTERN'), 0, [Match(0, 7, 0, b('PATERN'))]),
        ]:
            for chunk_size, delta in product(
                    [100, 2**10, 2**12, 2**18, 2**20],
                    sorted({-len(needle), -len(needle) + 1, -4, -2, -1, 0, 1})
            ):
                if len(needle) // (max_l_dist + 1) < 3:
                    # no ngrams search, so skip long searches which will be slow
                    if chunk_size > 2**10:
                        continue
                with self.subTest(
                        needle=needle, haystack_match=haystack_match, max_l_dist=max_l_dist,
                        chunk_size=chunk_size, delta=delta,
                ):
                    haystack = bytearray(chunk_size + 100)
                    haystack[chunk_size + delta:chunk_size + delta + len(haystack_match)] = haystack_match
                    with open(filename, 'wb') as f:
                        f.write(haystack)

                    with open(filename, 'rb') as f:
                        self.assertEqual(
                            find_near_matches_in_file(needle, f, max_l_dist=max_l_dist, _chunk_size=chunk_size),
                            [attr.evolve(match,
                                         start=match.start + chunk_size + delta,
                                         end=match.end + chunk_size + delta,
                                         matched=haystack_match)
                             for match in expected_matches]
                        )

                        f.seek(0)

                        self.assertEqual(
                            find_near_matches_in_file(needle, f, max_l_dist=max_l_dist, _chunk_size=chunk_size // 2),
                            [attr.evolve(match,
                                         start=match.start + chunk_size + delta,
                                         end=match.end + chunk_size + delta,
                                         matched=haystack_match)
                             for match in expected_matches]
                        )

                    with open(filename, 'r') as f:
                        _needle = needle.decode('utf-8')
                        self.assertEqual(
                            find_near_matches_in_file(_needle, f, max_l_dist=max_l_dist, _chunk_size=chunk_size),
                            [attr.evolve(match,
                                         start=match.start + chunk_size + delta,
                                         end=match.end + chunk_size + delta,
                                         matched=haystack.decode('utf-8'))
                             for match in expected_matches]
                        )

                    with io.open(filename, 'r', encoding='ascii') as f:
                        self.assertEqual(
                            find_near_matches_in_file(needle.decode('ascii'), f, max_l_dist=max_l_dist, _chunk_size=chunk_size),
                            [attr.evolve(match,
                                         start=match.start + chunk_size + delta,
                                         end=match.end + chunk_size + delta,
                                         matched=haystack.decode('utf-8'))
                             for match in expected_matches]
                        )

                        f.seek(0)

                        self.assertEqual(
                            find_near_matches_in_file(needle.decode('ascii'), f, max_l_dist=max_l_dist, _chunk_size=chunk_size // 2),
                            [attr.evolve(match,
                                         start=match.start + chunk_size + delta,
                                         end=match.end + chunk_size + delta,
                                         matched=haystack.decode('utf-8'))
                             for match in expected_matches]
                        )


# WARNING, DARK MAGIC AHEAD!
#
# Dynamically generate sub-classes of the TestFindNearMatchesAs* classes
# in tests.test_find_near_matches.  These sub-classes's setUp() monkey-patches
# fuzzysearch.find_near_matches(), replacing it with a wrapper for
# fuzzysearch.find_near_matches_in_file() using temporary files.
#
# TODO: replace this with something less magical

for class_name in filter(
    lambda x: re.match(r'^TestFindNearMatchesAs[a-zA-Z0-9_]+$', x),
    dir(tests.test_find_near_matches)
):
    new_class_name = class_name.replace('FindNearMatches',
                                        'FindNearMatchesInFile')
    orig_class = getattr(tests.test_find_near_matches, class_name)

    def setUp(self, _orig_class=orig_class):
        _orig_class.setUp(self)

        def find_near_matches_dropin(subsequence, sequence, *args, **kwargs):
            if isinstance(sequence, (tuple, list)):
                self.skipTest('skipping word-list tests with find_near_matches_in_file')
            try:
                from Bio.Seq import Seq
            except ImportError:
                pass
            else:
                if isinstance(sequence, Seq):
                    self.skipTest('skipping BioPython Seq tests with find_near_matches_in_file')

            tempfilepath = tempfile.mktemp()
            if isinstance(sequence, str):
                f = io.open(tempfilepath, 'w+', encoding='utf-8')
            else:
                f = open(tempfilepath, 'w+b')
            try:
                f.write(sequence)
                f.seek(0)
                return find_near_matches_in_file(subsequence, f, *args, **kwargs)
            finally:
                f.close()
                os.remove(tempfilepath)

        patcher = unittest.mock.patch(
            'tests.test_find_near_matches.find_near_matches',
            find_near_matches_dropin)
        self.addCleanup(patcher.stop)
        patcher.start()

    new_class = type(new_class_name, (orig_class,), {'setUp': setUp})
    globals()[new_class_name] = new_class
