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
            next_subseq_chars = subsequence[cand.subseq_index:cand.subseq_index + max_l_dist - cand.dist + 1]
            idx = next_subseq_chars.find(char)

            # if this sequence char is the candidate's next expected char
            if idx == 0:
                # if reached the end of the subsequence, return a match
                if cand.subseq_index + 1 == _subseq_len:
                    yield Match(cand.start, index + 1, cand.dist)
                # otherwise, update the candidate and keep it
                else:
                    new_candidates.append(cand._replace(
                        subseq_index=cand.subseq_index + 1,
                    ))

            # if this sequence char is *not* the candidate's next expected char
            else:
                # we can try skipping a sequence or sub-sequence char (or both),
                # unless this candidate has already skipped the maximum allowed
                # number of characters
                if cand.dist == max_l_dist:
                    continue

                # add a candidate skipping a sequence char
                new_candidates.append(cand._replace(dist=cand.dist + 1))

                if index + 1 < len(sequence) and cand.subseq_index + 1 < _subseq_len:
                    # add a candidate skipping both a sequence char and a
                    # subsequence char
                    new_candidates.append(cand._replace(
                        dist=cand.dist + 1,
                        subseq_index=cand.subseq_index+1,
                    ))

                # try skipping subsequence chars
                for n_skipped in xrange(1, max_l_dist - cand.dist + 1):
                    # if skipping n_skipped sub-sequence chars reaches the end
                    # of the sub-sequence, yield a match
                    if cand.subseq_index + n_skipped == _subseq_len:
                        yield Match(cand.start, index + 1, cand.dist + n_skipped)
                        break
                    # otherwise, if skipping n_skipped sub-sequence chars
                    # reaches a sub-sequence char identical to this sequence
                    # char, add a candidate skipping n_skipped sub-sequence
                    # chars
                    elif subsequence[cand.subseq_index + n_skipped] == char:
                        # add a candidate skipping n_skipped subsequence chars
                        new_candidates.append(cand._replace(
                            dist=cand.dist + n_skipped,
                            subseq_index=cand.subseq_index + n_skipped + 1,
                        ))
                        break
                # note: if the above loop ends without a break, that means that
                # no candidate could be added / yielded by skipping sub-sequence
                # chars

        candidates = new_candidates

    for cand in candidates:
        dist = cand.dist + len(subsequence) - cand.subseq_index
        if dist <= max_l_dist:
            yield Match(cand.start, len(sequence), dist)


def _find_all(subsequence, sequence, start_index=0, end_index=None):
    if isinstance(sequence, basestring):
        find = sequence.find
    else:
        raise TypeError('unsupported sequence type: %s' % type(sequence))

    index = find(subsequence, start_index, end_index)
    while index >= 0:
        yield index
        index = find(subsequence, index + 1, end_index)

def _expand(subsequence, sequence, max_l_dist):
    if not subsequence:
        return (0, 0)

    scores = range(max_l_dist + 1) + [None] * (len(subsequence) + 1 - (max_l_dist + 1))
    new_scores = [None] * (len(subsequence) + 1)
    min_score = None
    min_score_idx = None

    #print scores
    for seq_index, char in enumerate(sequence):
        new_scores[0] = scores[0] + 1
        for subseq_index in range(0, min(seq_index + max_l_dist, len(subsequence)-1)):
            new_scores[subseq_index + 1] = min(
                scores[subseq_index] + (0 if char == subsequence[subseq_index] else 1),
                scores[subseq_index + 1] + 1,
                new_scores[subseq_index] + 1,
            )
        subseq_index = min(seq_index + max_l_dist, len(subsequence) - 1)
        new_scores[subseq_index + 1] = last_score = min(
            scores[subseq_index] + (0 if char == subsequence[subseq_index] else 1),
            new_scores[subseq_index] + 1,
        )
        if subseq_index == len(subsequence) - 1 and (min_score is None or last_score <= min_score):
            min_score = last_score
            min_score_idx = seq_index

        scores, new_scores = new_scores, scores
        #print scores

    return (min_score, min_score_idx + 1) if min_score is not None and min_score <= max_l_dist else (None, None)


Ngram = namedtuple('Ngram', ['start', 'end'])

def _choose_search_range(subseq_len, seq_len, ngram, max_l_dist):
    start_index = max(0, ngram.start - max_l_dist)
    end_index = min(seq_len, seq_len - subseq_len + ngram.end + max_l_dist)
    return start_index, end_index

def find_near_matches_with_ngrams(subsequence, sequence, max_l_dist):
    ngram_len = len(subsequence) // (max_l_dist + 1)
    if ngram_len == 0:
        raise ValueError('the subsequence length must be greater than max_l_dist')

    ngrams = [
        Ngram(start, start + ngram_len)
        for start in range(0, len(subsequence) - ngram_len + 1, ngram_len)
    ]

    matches = []
    for ngram in ngrams:
        start_index, end_index = _choose_search_range(len(subsequence), len(sequence), ngram, max_l_dist)
        for index in _find_all(subsequence[ngram.start:ngram.end], sequence, start_index, end_index):
            # try to expand left and/or right according to n_ngram
            dist_left, left_expand_size = _expand(
                subsequence[:ngram.start][::-1],
                sequence[index - ngram.start - max_l_dist:index][::-1],
                max_l_dist,
            )
            if dist_left is None:
                continue
            dist_right, right_expand_size = _expand(
                subsequence[ngram.end:],
                sequence[index + ngram_len:index - ngram.start + len(subsequence) + max_l_dist],
                max_l_dist - dist_left,
            )
            if dist_right is None:
                continue
            assert dist_left + dist_right <= max_l_dist

            matches.append(Match(
                start=index - left_expand_size,
                end=index + ngram_len + right_expand_size,
                dist=dist_left + dist_right,
            ))

    # don't return overlapping matches; instead, group overlapping matches
    # together and return the best match from each group
    match_groups = group_matches(matches)
    best_matches = [get_best_match_in_group(group) for group in match_groups]
    return sorted(best_matches)


class Group(object):
    def __init__(self, match):
        self.start = match.start
        self.end = match.end
        self.matches = set([match])

    def is_match_in_group(self, match):
        return match in self.matches or \
            not (match.end <= self.start or match.start >= self.end)

    def does_overlap_group(self, other):
        return not (other.end <= self.start or other.start >= self.end)

    def add_match(self, match):
        self.matches.add(match)
        self.start = min(self.start, match.start)
        self.end = max(self.end, match.end)


def group_matches(matches):
    groups = []
    for match in matches:
        overlapping_groups = [g for g in groups if g.is_match_in_group(match)]
        if not overlapping_groups:
            groups.append(Group(match))
        elif len(overlapping_groups) == 1:
            groups[0].add_match(match)
        else:
            new_group = Group(match)
            for group in overlapping_groups:
                for match in group.matches:
                    new_group.add_match(match)
            groups = [g for g in groups if g not in overlapping_groups]
            groups.append(new_group)

    return [group.matches for group in groups]


def get_best_match_in_group(group):
    # return longest match amongst those with the shortest distance
    return min(group, key=lambda match: (match.dist, -(match.end - match.start)))
