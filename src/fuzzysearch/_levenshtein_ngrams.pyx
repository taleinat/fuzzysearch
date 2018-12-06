from libc.stdlib cimport malloc, free


__all__ = [
    'c_expand_short',
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
            elif c <= min_score:
                min_score = c
                min_score_idx = seq_index

        return (min_score, min_score_idx + 1) if min_score <= max_l_dist else (None, None)

    finally:
        free(scores)
