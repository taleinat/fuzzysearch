from libc.stdlib cimport malloc, free


__all__ = [
    'c_expand_short', 'c_expand_long'
]


def c_expand_short(subsequence, sequence, max_l_dist):
    """Straightforward implementation of partial match expansion."""
    # The following diagram shows the score calculation step.
    #
    # Each new score is the minimum of:
    #  * a OR a + 1 (substitution, if needed)
    #  * b + 1 (deletion, i.e. skipping a sequence character)
    #  * c + 1 (insertion, i.e. skipping a sub-sequence character)
    #
    # a -- +1 -> c
    #
    # |  \       |
    # |   \      |
    # +1  +1?    +1
    # |      \   |
    # v       ⌟  v
    #
    # b -- +1 -> scores[subseq_index]

    cdef unsigned int subseq_len = len(subsequence)
    if subseq_len == 0:
        return (0, 0)

    cdef size_t subseq_idx, seq_idx
    cdef unsigned int min_score = subseq_len
    cdef size_t min_score_idx = -1
    cdef unsigned int min_intermediate_score
    cdef unsigned int a, b, c

    # Initialize the scores array with values for just skipping sub-sequence
    # chars.
    cdef unsigned int *scores = <unsigned int *> malloc(subseq_len * sizeof(unsigned int));
    if scores is NULL:
        raise MemoryError()
    for subseq_idx in xrange(subseq_len):
        scores[subseq_idx] = (<unsigned int> subseq_idx) + 1

    try:
        for seq_index, seq_char in enumerate(sequence):
            # calculate scores, one for each character in the sub-sequence
            a = seq_index
            c = a + 1
            min_intermediate_score = c
            for subseq_index in xrange(subseq_len):
                b = scores[subseq_index]
                c = scores[subseq_index] = min(
                    a + (seq_char != subsequence[subseq_index]),
                    b + 1,
                    c + 1,
                )
                a = b
                if c < min_intermediate_score:
                    min_intermediate_score = c

            # bail early when it is impossible to find a better expansion
            if min_intermediate_score >= min_score:
                break

            # keep the minimum score found for matches of the entire sub-sequence
            if c <= min_score:
                min_score = c
                min_score_idx = seq_index

        return (min_score, min_score_idx + 1) if min_score <= max_l_dist else (None, None)

    finally:
        free(scores)


def c_expand_long(subsequence, sequence, max_l_dist):
    """Partial match expansion, optimized for long sub-sequences."""
    # The additional optimization in this version is to limit the part of
    # the sub-sequence inspected for each sequence character.  The start and
    # end of the iteration are limited to the range where the scores are
    # smaller than the maximum allowed distance.  Additionally, once a good
    # expansion has been found, the range is further reduced to where the
    # scores are smaller than the score of the best expansion found so far.

    cdef unsigned int subseq_len = len(subsequence)
    if subseq_len == 0:
        return (0, 0)

    cdef size_t subseq_idx, seq_idx
    cdef unsigned int min_score = subseq_len
    cdef size_t min_score_idx = -1
    cdef unsigned int a, b, c
    cdef unsigned int max_good_score = max_l_dist
    cdef size_t new_needle_idx_range_start = 0
    cdef size_t new_needle_idx_range_end = subseq_len - 1

    # Initialize the scores array with values for just skipping sub-sequence
    # chars.
    cdef unsigned int *scores = <unsigned int *> malloc(subseq_len * sizeof(unsigned int));
    if scores is NULL:
        raise MemoryError()
    for subseq_idx in xrange(subseq_len):
        scores[subseq_idx] = (<unsigned int> subseq_idx) + 1

    try:
        needle_idx_range_start = new_needle_idx_range_start
        needle_idx_range_end = min(subseq_len, new_needle_idx_range_end + 1)

        for seq_index, seq_char in enumerate(sequence):
            # calculate scores, one for each character in the sub-sequence
            a = seq_index
            c = a + 1

            if c <= max_good_score:
                new_needle_idx_range_start = 0
                new_needle_idx_range_end = 0
            else:
                new_needle_idx_range_start = -1
                new_needle_idx_range_end = -1

            for subseq_index in xrange(subseq_len):
                b = scores[subseq_index]
                c = scores[subseq_index] = min(
                    a + (seq_char != subsequence[subseq_index]),
                    b + 1,
                    c + 1,
                )
                a = b

                if c <= max_good_score:
                    if new_needle_idx_range_start == -1:
                        new_needle_idx_range_start = subseq_index
                    new_needle_idx_range_end = max(
                        new_needle_idx_range_end,
                        subseq_index + 1 + (max_good_score - c),
                    )

            # bail early when it is impossible to find a better expansion
            if new_needle_idx_range_start == -1:
                break

            # keep the minimum score found for matches of the entire sub-sequence
            if c <= min_score:
                min_score = c
                min_score_idx = seq_index
                if min_score < max_good_score:
                    max_good_score = min_score

        return (min_score, min_score_idx + 1) if min_score <= max_l_dist else (None, None)

    finally:
        free(scores)
