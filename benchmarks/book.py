import contextlib
import io
import os.path

from fuzzysearch import find_near_matches_in_file


book_file_path = os.path.join(
    os.path.dirname(__file__),
    'The Adventures of Huckleberry Finn.txt',
)


def search(substring, max_l_dist, as_binary=False):
    if as_binary:
        f = open(book_file_path, 'rb')
    else:
        f = io.open(book_file_path, encoding='utf-8')

    with contextlib.closing(f):
        for match in find_near_matches_in_file(substring, f, max_l_dist=max_l_dist):
            pass
