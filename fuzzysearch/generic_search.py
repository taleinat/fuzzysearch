from collections import namedtuple
from fuzzysearch.common import Match


GenericSearchCandidate = namedtuple(
    'GenericSearchCandidate',
    ['start', 'subseq_index', 'l_dist', 'n_subs', 'n_ins', 'n_dels'],
)


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

    candidates = []
    for index, char in enumerate(sequence):
        candidates.append(GenericSearchCandidate(index, 0, 0, 0, 0, 0))
        new_candidates = []

        for cand in candidates:
            # if this sequence char is the candidate's next expected char
            if char == subsequence[cand.subseq_index]:
                # if reached the end of the subsequence, return a match
                if cand.subseq_index + 1 == _subseq_len:
                    yield Match(cand.start, index + 1, cand.l_dist)
                # otherwise, update the candidate's subseq_index and keep it
                else:
                    new_candidates.append(cand._replace(
                        subseq_index=cand.subseq_index + 1,
                    ))

            # if this sequence char is *not* the candidate's next expected char
            else:
                # we can try skipping a sequence or sub-sequence char (or both),
                # unless this candidate has already skipped the maximum allowed
                # number of characters
                if cand.l_dist == max_l_dist:
                    continue

                if cand.n_ins < max_insertions:
                    # add a candidate skipping a sequence char
                    new_candidates.append(cand._replace(
                        n_ins=cand.n_ins + 1,
                        l_dist=cand.l_dist + 1,
                    ))

                if cand.subseq_index + 1 < _subseq_len:
                    if cand.n_subs < max_substitutions:
                        # add a candidate skipping both a sequence char and a
                        # subsequence char
                        new_candidates.append(cand._replace(
                            n_subs=cand.n_subs + 1,
                            subseq_index=cand.subseq_index + 1,
                            l_dist=cand.l_dist + 1,
                        ))
                    elif cand.n_dels < max_deletions and cand.n_ins < max_insertions:
                        # add a candidate skipping both a sequence char and a
                        # subsequence char
                        new_candidates.append(cand._replace(
                            n_ins=cand.n_ins + 1,
                            n_dels=cand.n_dels + 1,
                            subseq_index=cand.subseq_index + 1,
                            l_dist=cand.l_dist + 1,
                        ))
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
                            new_candidates.append(cand._replace(
                                n_dels=cand.n_dels + n_skipped,
                                subseq_index=cand.subseq_index + 1 + n_skipped,
                                l_dist=cand.l_dist + n_skipped,
                            ))
                        break
                # note: if the above loop ends without a break, that means that
                # no candidate could be added / yielded by skipping sub-sequence
                # chars

        candidates = new_candidates

    for cand in candidates:
        # note: index + 1 == length(sequence)
        n_skipped = _subseq_len - cand.subseq_index
        if cand.n_dels + n_skipped <= max_deletions and \
           cand.l_dist + n_skipped <= max_l_dist:
            yield Match(cand.start, index + 1, cand.l_dist + n_skipped)
