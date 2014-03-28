from fuzzysearch.common import Match

cdef struct GenericSearchCandidate:
    int start, subseq_index, l_dist, n_subs, n_ins, n_dels


def find_near_matches_generic_linear_programming(subsequence, sequence,
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
    if not subsequence:
        raise ValueError('Given subsequence is empty!')

    # optimization: prepare some often used things in advance
    _subseq_len = len(subsequence)

    maxes_sum = sum(
        (x if x is not None else 0)
        for x in [max_substitutions, max_insertions, max_deletions]
    )
    if max_l_dist is None or max_l_dist >= maxes_sum:
        max_l_dist = maxes_sum

    cdef GenericSearchCandidate[1000] _candidates1
    cdef GenericSearchCandidate[1000] _candidates2
    cdef GenericSearchCandidate* candidates = _candidates1
    cdef GenericSearchCandidate* new_candidates = _candidates2
    cdef GenericSearchCandidate* _tmp
    cdef GenericSearchCandidate cand
    cdef int n_candidates = 0
    cdef int n_new_candidates = 0
    cdef int n_cand

    for index, char in enumerate(sequence):
        candidates[n_candidates] = GenericSearchCandidate(index, 0, 0, 0, 0, 0)
        n_candidates += 1

        for n_cand in xrange(n_candidates):
            cand = candidates[n_cand]
            # if this sequence char is the candidate's next expected char
            if char == subsequence[cand.subseq_index]:
                # if reached the end of the subsequence, return a match
                if cand.subseq_index + 1 == _subseq_len:
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

                if cand.subseq_index + 1 < _subseq_len:
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
                        yield Match(cand.start, index + 1, cand.l_dist + 1)

                # try skipping subsequence chars
                for n_skipped in xrange(1, min(max_deletions - cand.n_dels, max_l_dist - cand.l_dist) + 1):
                    # if skipping n_dels sub-sequence chars reaches the end
                    # of the sub-sequence, yield a match
                    if cand.subseq_index + n_skipped == _subseq_len:
                        yield Match(cand.start, index + 1,
                                    cand.l_dist + n_skipped)
                        break
                    # otherwise, if skipping n_skipped sub-sequence chars
                    # reaches a sub-sequence char identical to this sequence
                    # char ...
                    elif subsequence[cand.subseq_index + n_skipped] == char:
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

    for n_cand in xrange(n_candidates):
        cand = candidates[n_cand]
        # note: index + 1 == length(sequence)
        n_skipped = _subseq_len - cand.subseq_index
        if cand.n_dels + n_skipped <= max_deletions and \
           cand.l_dist + n_skipped <= max_l_dist:
            yield Match(cand.start, index + 1, cand.l_dist + n_skipped)
