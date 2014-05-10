from sys import maxint
import six
from fuzzysearch.common import Match
from libc.stdlib cimport malloc, free, realloc

cdef extern from "kmp.h":
    struct KMPstate:
        pass # no need to specify the fields if they aren't accessed directly

    void preKMP(const char *subsequence, int subsequence_len, int *kmpNext)

    KMPstate KMP_init(const char *subseq, int subseq_len,
                      const char *seq, int seq_len,
                      int *kmpNext)

    const char* KMP_find_next(KMPstate *kmp_state)

__all__ = [
    'c_find_near_matches_generic_linear_programming',
    'c_find_near_matches_generic_ngrams',
]


cdef struct GenericSearchCandidate:
    int start, subseq_index, l_dist, n_subs, n_ins, n_dels


ALLOWED_TYPES = (six.binary_type, bytearray)
try:
    from Bio.Seq import Seq
except ImportError:
    pass
else:
    ALLOWED_TYPES += (Seq,)


def c_find_near_matches_generic_linear_programming(subsequence, sequence,
                                                   max_substitutions,
                                                   max_insertions,
                                                   max_deletions,
                                                   max_l_dist=None):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the maximum allowed number of character substitutions
    * the maximum allowed number of new characters inserted
    * and the maximum allowed number of character deletions
    * the total number of substitutions, insertions and deletions
    """
    if not isinstance(sequence, ALLOWED_TYPES):
        raise TypeError('sequence is of invalid type %s' % type(subsequence))
    if not isinstance(subsequence, ALLOWED_TYPES):
        raise TypeError('subsequence is of invalid type %s' % type(subsequence))

    if not subsequence:
        raise ValueError('Given subsequence is empty!')

    cdef const char *c_subsequence = subsequence
    cdef const char *c_sequence = sequence

    return _c_find_near_matches_generic_linear_programming(
        c_subsequence, len(subsequence),
        c_sequence, len(sequence),
        max_substitutions if max_substitutions is not None else (1<<29),
        max_insertions if max_insertions is not None else (1<<29),
        max_deletions if max_deletions is not None else (1<<29),
        max_l_dist if max_l_dist is not None else (1<<29),
    )

# The following MUST be a cdef, otherwise Cython copies the sequence and
# subsequence strings, which means if they contain null bytes the data after
# the first null byte will not be copied.
cdef _c_find_near_matches_generic_linear_programming(
        const char* subsequence, size_t subseq_len,
        const char* sequence, size_t seq_len,
        unsigned int max_substitutions,
        unsigned int max_insertions,
        unsigned int max_deletions,
        unsigned int max_l_dist,
):
    cdef unsigned int subseq_len_minus_one = subseq_len - 1

    cdef size_t alloc_size
    cdef GenericSearchCandidate* candidates
    cdef GenericSearchCandidate* new_candidates
    cdef GenericSearchCandidate* _tmp
    cdef GenericSearchCandidate cand
    cdef size_t n_candidates = 0
    cdef size_t n_new_candidates = 0
    cdef size_t n_cand

    alloc_size = min(10, subseq_len * 3 + 1)
    candidates = <GenericSearchCandidate *> malloc(alloc_size * sizeof(GenericSearchCandidate))
    if candidates is NULL:
        raise MemoryError()
    new_candidates = <GenericSearchCandidate *> malloc(alloc_size * sizeof(GenericSearchCandidate))
    if candidates is NULL:
        free(candidates)
        raise MemoryError()

    matches = []

    cdef size_t index
    cdef char seq_char

    try:
        index = 0
        have_realloced = False
        for seq_char in sequence[:seq_len]:
            candidates[n_candidates] = GenericSearchCandidate(index, 0, 0, 0, 0, 0)
            n_candidates += 1

            for n_cand in xrange(n_candidates):
                cand = candidates[n_cand]

                if n_new_candidates + 4 > alloc_size:
                    alloc_size *= 2
                    _tmp = <GenericSearchCandidate *>realloc(new_candidates, alloc_size * sizeof(GenericSearchCandidate))
                    if _tmp is NULL:
                        raise MemoryError()
                    new_candidates = _tmp
                    have_realloced = True

                # if this sequence char is the candidate's next expected char
                if seq_char == subsequence[cand.subseq_index]:
                    # if reached the end of the subsequence, return a match
                    if cand.subseq_index == subseq_len_minus_one:
                        matches.append(Match(cand.start, index + 1, cand.l_dist))
                    # otherwise, update the candidate's subseq_index and keep it
                    else:
                        new_candidates[n_new_candidates] = GenericSearchCandidate(
                            cand.start, cand.subseq_index + 1,
                            cand.l_dist, cand.n_subs,
                            cand.n_ins, cand.n_dels,
                        )
                        n_new_candidates += 1

                # if this sequence char is *not* the candidate's next expected char
                else:
                    # we can try skipping a sequence or sub-sequence char (or both),
                    # unless this candidate has already skipped the maximum allowed
                    # number of characters
                    if cand.l_dist == max_l_dist:
                        continue

                    if cand.n_ins < max_insertions:
                        # add a candidate skipping a sequence char
                        new_candidates[n_new_candidates] = GenericSearchCandidate(
                            cand.start, cand.subseq_index,
                            cand.l_dist + 1, cand.n_subs,
                            cand.n_ins + 1, cand.n_dels,
                        )
                        n_new_candidates += 1

                    if cand.subseq_index + 1 < subseq_len:
                        if cand.n_subs < max_substitutions:
                            # add a candidate skipping both a sequence char and a
                            # subsequence char
                            new_candidates[n_new_candidates] = GenericSearchCandidate(
                                cand.start, cand.subseq_index + 1,
                                cand.l_dist + 1, cand.n_subs + 1,
                                cand.n_ins, cand.n_dels,
                            )
                            n_new_candidates += 1
                        elif cand.n_dels < max_deletions and cand.n_ins < max_insertions:
                            # add a candidate skipping both a sequence char and a
                            # subsequence char
                            new_candidates[n_new_candidates] = GenericSearchCandidate(
                                cand.start, cand.subseq_index + 1,
                                cand.l_dist + 1, cand.n_subs,
                                cand.n_ins + 1, cand.n_dels + 1,
                            )
                            n_new_candidates += 1
                    else:
                        # cand.subseq_index == _subseq_len - 1
                        if (
                                cand.n_subs < max_substitutions or
                                (
                                    cand.n_dels < max_deletions and
                                    cand.n_ins < max_insertions
                                )
                        ):
                            matches.append(Match(cand.start, index + 1, cand.l_dist + 1))

                    # try skipping subsequence chars
                    for n_skipped in xrange(1, min(max_deletions - cand.n_dels, max_l_dist - cand.l_dist) + 1):
                        # if skipping n_dels sub-sequence chars reaches the end
                        # of the sub-sequence, yield a match
                        if cand.subseq_index + n_skipped == subseq_len:
                            matches.append(Match(cand.start, index + 1,
                                                 cand.l_dist + n_skipped))
                            break
                        # otherwise, if skipping n_skipped sub-sequence chars
                        # reaches a sub-sequence char identical to this sequence
                        # char ...
                        elif seq_char == subsequence[cand.subseq_index + n_skipped]:
                            # if this is the last char of the sub-sequence, yield
                            # a match
                            if cand.subseq_index + n_skipped + 1 == subseq_len:
                                matches.append(Match(cand.start, index + 1,
                                                     cand.l_dist + n_skipped))
                            # otherwise add a candidate skipping n_skipped
                            # subsequence chars
                            else:
                                new_candidates[n_new_candidates] = GenericSearchCandidate(
                                    cand.start, cand.subseq_index + 1 + n_skipped,
                                    cand.l_dist + n_skipped, cand.n_subs,
                                    cand.n_ins, cand.n_dels + n_skipped,
                                )
                                n_new_candidates += 1
                            break
                    # note: if the above loop ends without a break, that means that
                    # no candidate could be added / yielded by skipping sub-sequence
                    # chars

            # new_candidates = candidates; candidates = []
            _tmp = candidates
            candidates = new_candidates
            new_candidates = _tmp
            n_candidates = n_new_candidates
            n_new_candidates = 0

            if have_realloced:
                have_realloced = False
                _tmp = <GenericSearchCandidate *>realloc(new_candidates, alloc_size * sizeof(GenericSearchCandidate))
                if _tmp is NULL:
                    raise MemoryError()
                new_candidates = _tmp

            index += 1

        for n_cand in xrange(n_candidates):
            cand = candidates[n_cand]
            # note: index == length(sequence)
            n_skipped = subseq_len - cand.subseq_index
            if cand.n_dels + n_skipped <= max_deletions and \
               cand.l_dist + n_skipped <= max_l_dist:
                matches.append(Match(cand.start, index, cand.l_dist + n_skipped))

    finally:
        free(candidates)
        free(new_candidates)

    return matches



def c_find_near_matches_generic_ngrams(subsequence, sequence,
                                       max_substitutions, max_insertions,
                                       max_deletions, max_l_dist=None):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the maximum allowed number of character substitutions
    * the maximum allowed number of new characters inserted
    * and the maximum allowed number of character deletions
    * the total number of substitutions, insertions and deletions
    """
    if not isinstance(sequence, ALLOWED_TYPES):
        raise TypeError('sequence is of invalid type %s' % type(subsequence))
    if not isinstance(subsequence, ALLOWED_TYPES):
        raise TypeError('subsequence is of invalid type %s' % type(subsequence))

    if not subsequence:
        raise ValueError('Given subsequence is empty!')

    # optimization: prepare some often used things in advance
    cdef size_t _subseq_len = len(subsequence)
    cdef size_t _subseq_len_minus_one = _subseq_len - 1
    cdef size_t _seq_len = len(sequence)

    cdef unsigned int c_max_substitutions = max_substitutions if max_substitutions is not None else (1<<29)
    cdef unsigned int c_max_insertions = max_insertions if max_insertions is not None else (1<<29)
    cdef unsigned int c_max_deletions = max_deletions if max_deletions is not None else (1<<29)

    # TODO: write a good comment
    cdef unsigned int c_max_l_dist = min(
        max_l_dist if max_l_dist is not None else (1<<29),
        c_max_substitutions + c_max_insertions + c_max_deletions,
    )

    cdef const char* c_sequence = sequence
    cdef const char* c_subsequence = subsequence

    cdef size_t ngram_len = _subseq_len // (c_max_l_dist + 1)
    if ngram_len == 0:
        raise ValueError('the subsequence length must be greater than max_l_dist')

    cdef int index, small_search_start_index
    cdef size_t ngram_start

    cdef const char *match_ptr
    cdef int *kmpNext
    cdef KMPstate kmp_state
    kmpNext = <int *> malloc(ngram_len * sizeof(int))
    if kmpNext is NULL:
        raise MemoryError()

    try:
        matches = []
        for ngram_start in xrange(0, _subseq_len - ngram_len + 1, ngram_len):
            preKMP(c_subsequence + ngram_start, ngram_len, kmpNext)

            kmp_state = KMP_init(c_subsequence + ngram_start, ngram_len, c_sequence, _seq_len, kmpNext)
            match_ptr = KMP_find_next(&kmp_state)
            while match_ptr != NULL:
                small_search_start_index = (match_ptr - c_sequence) - ngram_start - c_max_l_dist
                small_search_length = _subseq_len + (2 * c_max_l_dist)
                if small_search_start_index < 0:
                    small_search_length += small_search_start_index
                    small_search_start_index = 0
                if small_search_start_index + small_search_length > _seq_len:
                    small_search_length = _seq_len - small_search_start_index
                # try to expand left and/or right according to n_ngram
                for match in _c_find_near_matches_generic_linear_programming(
                    c_subsequence, _subseq_len,
                    c_sequence + small_search_start_index,
                    small_search_length,
                    c_max_substitutions, c_max_insertions, c_max_deletions, c_max_l_dist,
                ):
                    matches.append(match._replace(
                        start=match.start + small_search_start_index,
                        end=match.end + small_search_start_index,
                    ))
                match_ptr = KMP_find_next(&kmp_state)

    finally:
        free(kmpNext)

    return matches