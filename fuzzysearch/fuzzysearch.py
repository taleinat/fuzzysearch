from collections import namedtuple

Candidate = namedtuple('Candidate', ['start', 'subseq_index', 'dist'])
Match = namedtuple('Match', ['start', 'end', 'dist'])


def _prepare_init_candidates_dict(subsequence, max_l_dist):
    return dict((
        (char, index)
        for (index, char) in enumerate(subsequence[:max_l_dist + 1])
        if char not in subsequence[:index]
    ))

def find_near_matches(subsequence, sequence, max_l_dist=0):
    if not subsequence:
        raise ValueError('Given subsequence is empty!')

    # optimization: prepare some often used things in advance
    _init_candidates_dict = _prepare_init_candidates_dict(subsequence, max_l_dist)
    _subseq_len = len(subsequence)

    candidates = []
    last_candidate_init_index = -1
    for index, char in enumerate(sequence):
        new_candidates = []

        idx_in_subseq = _init_candidates_dict.get(char, None)
        if idx_in_subseq is not None:
        #if idx_in_subseq is not None and (
        #        idx_in_subseq == 0 or (
        #            idx_in_subseq < index - last_candidate_init_index
        #            #and
        #            #not any(c.subseq_index < idx_in_subseq for c in candidates)
        #        )
        #):
            new_candidates.append(Candidate(index, idx_in_subseq + 1, idx_in_subseq))
            #last_candidate_init_index = index

        for cand in candidates:
            if char == subsequence[cand.subseq_index]:
                if cand.subseq_index + 1 == _subseq_len:
                    yield Match(cand.start, index + 1, cand.dist)
                else:
                    new_candidates.append(cand._replace(
                        subseq_index=cand.subseq_index + 1,
                    ))
            else:
                if cand.dist == max_l_dist or cand.subseq_index == 0:
                    continue
                # add a candidate skipping a sequence char
                new_candidates.append(cand._replace(dist=cand.dist + 1))
                # try skipping subsequence chars
                for n_skipped in xrange(1, max_l_dist - cand.dist + 1):
                    if cand.subseq_index + n_skipped == _subseq_len:
                        yield Match(cand.start, index + 1, cand.dist + n_skipped)
                        break
                    elif subsequence[cand.subseq_index + n_skipped] == char:
                        # add a candidate skipping n_skipped subsequence chars
                        new_candidates.append(cand._replace(
                            dist=cand.dist + n_skipped,
                            subseq_index=cand.subseq_index + n_skipped,
                        ))
                        break
        candidates = new_candidates
