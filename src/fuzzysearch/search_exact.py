from functools import wraps

from fuzzysearch.common import FuzzySearchBase, Match
from fuzzysearch.compat import text_type, xrange


__all__ = [
    'search_exact',
    'ExactSearch',
]


CLASSES_WITH_INDEX = (list, tuple)
CLASSES_WITH_FIND = (bytes, bytearray, text_type)

try:
    from Bio.Seq import Seq
except ImportError:
    pass
else:
    CLASSES_WITH_FIND += (Seq,)


def search_exact(subsequence, sequence, start_index=0, end_index=None):
    if not subsequence:
        raise ValueError('subsequence must not be empty')

    if end_index is None:
        end_index = len(sequence)

    if isinstance(sequence, CLASSES_WITH_FIND):
        def find_in_index_range(start_index):
            return sequence.find(subsequence, start_index, end_index)
    elif isinstance(sequence, CLASSES_WITH_INDEX):
        first_item = subsequence[0]
        first_item_last_index = end_index - (len(subsequence) - 1)
        def find_in_index_range(start_index):
            while True:
                try:
                    first_index = sequence.index(first_item, start_index, first_item_last_index)
                    start_index = first_index + 1
                except ValueError:
                    return -1
                for subseq_index in xrange(1, len(subsequence)):
                    if sequence[first_index + subseq_index] != subsequence[subseq_index]:
                        break
                else:
                    return first_index
    else:
        raise TypeError('unsupported sequence type: %s' % type(sequence))

    index = find_in_index_range(start_index)
    while index >= 0:
        yield index
        index = find_in_index_range(index + 1)


try:
    from fuzzysearch._common import search_exact_byteslike
except ImportError:
    pass
else:
    _search_exact = search_exact
    @wraps(_search_exact)
    def search_exact(subsequence, sequence, start_index=0, end_index=None):
        if end_index is None:
            end_index = len(sequence)

        try:
            return search_exact_byteslike(subsequence, sequence,
                                          start_index, end_index)
        except (TypeError, UnicodeEncodeError):
            return _search_exact(subsequence, sequence, start_index, end_index)


class ExactSearch(FuzzySearchBase):
    @classmethod
    def search(cls, subsequence, sequence, search_params):
        for index in search_exact(subsequence, sequence):
            yield Match(index, index + len(subsequence), 0,
                        sequence[index:index + len(subsequence)])

    @classmethod
    def extra_items_for_chunked_search(cls, subsequence, search_params):
        return 0
