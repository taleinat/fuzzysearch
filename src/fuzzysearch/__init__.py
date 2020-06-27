"""A library for finding approximate subsequence matches.

Contains several implementations of fuzzy sub-sequence search functions. Such
functions find parts of a sequence which match a given sub-sequence up to a
given maximum Levenshtein distance.

The simplest use is via the find_near_matches utility function, which chooses
a suitable fuzzy search implementation based on the given parameters.

Example:
>>> find_near_matches('PATTERN', '---PATERN---', max_l_dist=1)
[Match(start=3, end=9, dist=1, matched='PATERN')]
"""
__author__ = 'Tal Einat'
__email__ = 'taleinat@gmail.com'
__version__ = '0.7.3'

__all__ = [
    'find_near_matches',
    'find_near_matches_in_file',
    'Match',
]

import io

from fuzzysearch.common import Match, LevenshteinSearchParams
from fuzzysearch.generic_search import GenericSearch
from fuzzysearch.levenshtein import LevenshteinSearch
from fuzzysearch.search_exact import ExactSearch
from fuzzysearch.substitutions_only import SubstitutionsOnlySearch

import attr


def find_near_matches(subsequence, sequence,
                      max_substitutions=None,
                      max_insertions=None,
                      max_deletions=None,
                      max_l_dist=None):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the maximum allowed number of character substitutions
    * the maximum allowed number of new characters inserted
    * and the maximum allowed number of character deletions
    * the total number of substitutions, insertions and deletions
      (a.k.a. the Levenshtein distance)
    """
    search_params = LevenshteinSearchParams(max_substitutions,
                                            max_insertions,
                                            max_deletions,
                                            max_l_dist)
    search_class = choose_search_class(search_params)
    matches = search_class.search(subsequence, sequence, search_params)
    return search_class.consolidate_matches(matches)


def choose_search_class(search_params):
    max_substitutions, max_insertions, max_deletions, max_l_dist = search_params.unpacked

    # if the limitations are so strict that only exact matches are allowed,
    # use search_exact()
    if max_l_dist == 0:
        return ExactSearch

    # if only substitutions are allowed, use find_near_matches_substitutions()
    elif max_insertions == 0 and max_deletions == 0:
        return SubstitutionsOnlySearch

    # if it is enough to just take into account the maximum Levenshtein
    # distance, use find_near_matches_levenshtein()
    elif max_l_dist <= min(
        (max_substitutions if max_substitutions is not None else (1 << 29)),
        (max_insertions if max_insertions is not None else (1 << 29)),
        (max_deletions if max_deletions is not None else (1 << 29)),
    ):
        return LevenshteinSearch

    # if none of the special cases above are met, use the most generic version
    else:
        return GenericSearch


def find_near_matches_in_file(subsequence, sequence_file,
                              max_substitutions=None,
                              max_insertions=None,
                              max_deletions=None,
                              max_l_dist=None,
                              _chunk_size=2**20):
    """search for near-matches of subsequence in a file

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the maximum allowed number of character substitutions
    * the maximum allowed number of new characters inserted
    * and the maximum allowed number of character deletions
    * the total number of substitutions, insertions and deletions
      (a.k.a. the Levenshtein distance)
    """
    search_params = LevenshteinSearchParams(max_substitutions,
                                            max_insertions,
                                            max_deletions,
                                            max_l_dist)
    search_class = choose_search_class(search_params)

    if (
            'b' in getattr(sequence_file, 'mode', '')
            or
            isinstance(sequence_file, io.RawIOBase)
    ):
        matches = _search_binary_file(subsequence,
                                      sequence_file,
                                      search_params,
                                      search_class,
                                      _chunk_size=_chunk_size)
    else:
        matches = _search_unicode_file(subsequence,
                                       sequence_file,
                                       search_params,
                                       search_class,
                                       _chunk_size=_chunk_size)

    return search_class.consolidate_matches(matches)


def _search_binary_file(subsequence, sequence_file, search_params, search_class,
                        _chunk_size):
    if not subsequence:
        raise ValueError('subsequence must not be empty')

    CHUNK_SIZE = _chunk_size
    keep_bytes = (
        len(subsequence) - 1 +
        search_class.extra_items_for_chunked_search(subsequence, search_params)
    )

    # To allocate memory only once, we'll use a pre-allocated bytearray and
    # file.readinto().  Furthermore, since we'll need to keep part of each
    # chunk along with the next chunk, we'll use a memoryview of the bytearray
    # to move data around within a single block of memory and thus avoid
    # allocations.
    chunk_bytes = bytearray(CHUNK_SIZE)
    chunk_memview = memoryview(chunk_bytes)

    # The search will be done with bytearray objects.  Note that in Python 2,
    # getting an item from a bytes object returns a string (rather than an
    # int as in Python 3), so we explicitly convert the sub-sequence to a
    # bytearray in case it is a bytes/str object.
    subseq_bytearray = bytearray(subsequence)

    n_read = sequence_file.readinto(chunk_memview)
    offset = 0
    chunk_len = n_read
    while n_read:
        search_bytes = chunk_bytes if chunk_len == CHUNK_SIZE else chunk_bytes[:chunk_len]
        for match in search_class.search(subseq_bytearray, search_bytes, search_params):
            yield attr.evolve(match,
                              start=match.start + offset,
                              end=match.end + offset)

        if keep_bytes > 0:
            n_to_keep = min(keep_bytes, chunk_len)
            chunk_memview[:n_to_keep] = chunk_memview[chunk_len - n_to_keep:chunk_len]
        else:
            n_to_keep = 0
        offset += chunk_len - n_to_keep
        n_read = sequence_file.readinto(chunk_memview[n_to_keep:])
        chunk_len = n_to_keep + n_read


def _search_unicode_file(subsequence, sequence_file, search_params, search_class,
                         _chunk_size):
    if not subsequence:
        raise ValueError('subsequence must not be empty')

    CHUNK_SIZE = _chunk_size
    keep_chars = (
        len(subsequence) - 1 +
        search_class.extra_items_for_chunked_search(subsequence, search_params)
    )

    chunk = sequence_file.read(CHUNK_SIZE)
    offset = 0
    while chunk:
        for match in search_class.search(subsequence, chunk, search_params):
            yield attr.evolve(match,
                              start=match.start + offset,
                              end=match.end + offset)

        n_to_keep = min(keep_chars, len(chunk))
        offset += len(chunk) - n_to_keep
        if n_to_keep:
            chunk = chunk[-n_to_keep:] + sequence_file.read(CHUNK_SIZE)
            if len(chunk) == n_to_keep:
                break
        else:
            chunk = sequence_file.read(CHUNK_SIZE)
