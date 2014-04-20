import sys
import six
from fuzzysearch.common import Match
from libc.stdlib cimport malloc, free, realloc


__all__ = ['c_find_near_matches_generic_linear_programming']


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

    # optimization: prepare some often used things in advance
    cdef int _subseq_len = len(subsequence)
    cdef int _subseq_len_minus_one = _subseq_len - 1

    maxes_sum = sum(
        (x if x is not None else 0)
        for x in [max_substitutions, max_insertions, max_deletions]
    )
    if max_l_dist is None or max_l_dist >= maxes_sum:
        max_l_dist = maxes_sum

    cdef c_max_l_dist = max_l_dist
    cdef c_max_substitutions = max_substitutions
    cdef c_max_insertions = max_insertions
    cdef c_max_deletions = max_deletions

    cdef alloc_size
    cdef GenericSearchCandidate* candidates
    cdef GenericSearchCandidate* new_candidates
    cdef GenericSearchCandidate* _tmp
    cdef GenericSearchCandidate cand
    cdef int n_candidates = 0
    cdef int n_new_candidates = 0
    cdef int n_cand

    cdef char* c_sequence = sequence
    cdef char* c_subsequence = subsequence
    cdef char char

    alloc_size = min(10, _subseq_len * 3 + 1)
    candidates = <GenericSearchCandidate *> malloc(alloc_size * sizeof(GenericSearchCandidate))
    if candidates is NULL:
        raise MemoryError()
    new_candidates = <GenericSearchCandidate *> malloc(alloc_size * sizeof(GenericSearchCandidate))
    if candidates is NULL:
        free(candidates)
        raise MemoryError()

    cdef unsigned int index
    try:
        index = 0
        have_realloced = False
        for char in c_sequence[:len(sequence)]:
            candidates[n_candidates] = GenericSearchCandidate(index, 0, 0, 0, 0, 0)
            n_candidates += 1

            for n_cand in xrange(n_candidates):
                cand = candidates[n_cand]

                if n_new_candidates + 4 > alloc_size:
                    alloc_size += alloc_size // 2
                    _tmp = <GenericSearchCandidate *>realloc(new_candidates, alloc_size * sizeof(GenericSearchCandidate))
                    if _tmp is NULL:
                        raise MemoryError()
                    new_candidates = _tmp
                    have_realloced = True

                # if this sequence char is the candidate's next expected char
                if char == c_subsequence[cand.subseq_index]:
                    # if reached the end of the subsequence, return a match
                    if cand.subseq_index == _subseq_len_minus_one:
                        yield Match(cand.start, index + 1, cand.l_dist)
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
                    if cand.l_dist == c_max_l_dist:
                        continue

                    if cand.n_ins < c_max_insertions:
                        # add a candidate skipping a sequence char
                        new_candidates[n_new_candidates] = GenericSearchCandidate(
                            cand.start, cand.subseq_index,
                            cand.l_dist + 1, cand.n_subs,
                            cand.n_ins + 1, cand.n_dels,
                        )
                        n_new_candidates += 1

                    if cand.subseq_index + 1 < _subseq_len:
                        if cand.n_subs < c_max_substitutions:
                            # add a candidate skipping both a sequence char and a
                            # subsequence char
                            new_candidates[n_new_candidates] = GenericSearchCandidate(
                                cand.start, cand.subseq_index + 1,
                                cand.l_dist + 1, cand.n_subs + 1,
                                cand.n_ins, cand.n_dels,
                            )
                            n_new_candidates += 1
                        elif cand.n_dels < c_max_deletions and cand.n_ins < c_max_insertions:
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
                                cand.n_subs < c_max_substitutions or
                                (
                                    cand.n_dels < c_max_deletions and
                                    cand.n_ins < c_max_insertions
                                )
                        ):
                            yield Match(cand.start, index + 1, cand.l_dist + 1)

                    # try skipping subsequence chars
                    for n_skipped in xrange(1, min(c_max_deletions - cand.n_dels, c_max_l_dist - cand.l_dist) + 1):
                        # if skipping n_dels sub-sequence chars reaches the end
                        # of the sub-sequence, yield a match
                        if cand.subseq_index + n_skipped == _subseq_len:
                            yield Match(cand.start, index + 1,
                                        cand.l_dist + n_skipped)
                            break
                        # otherwise, if skipping n_skipped sub-sequence chars
                        # reaches a sub-sequence char identical to this sequence
                        # char ...
                        elif char == c_subsequence[cand.subseq_index + n_skipped]:
                            # if this is the last char of the sub-sequence, yield
                            # a match
                            if cand.subseq_index + n_skipped + 1 == _subseq_len:
                                yield Match(cand.start, index + 1,
                                            cand.l_dist + n_skipped)
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
            n_skipped = _subseq_len - cand.subseq_index
            if cand.n_dels + n_skipped <= c_max_deletions and \
               cand.l_dist + n_skipped <= c_max_l_dist:
                yield Match(cand.start, index, cand.l_dist + n_skipped)

    finally:
        free(candidates)
        free(new_candidates)
