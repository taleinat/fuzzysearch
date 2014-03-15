from fuzzysearch.common import Match, Ngram, \
    group_matches, get_best_match_in_group, search_exact


__all__ = ['find_near_matches_levenshtein_ngrams']


def _expand(subsequence, sequence, max_l_dist):
    if not subsequence:
        return (0, 0)

    scores = range(max_l_dist + 1) + [None] * (len(subsequence) + 1 - (max_l_dist + 1))
    new_scores = [None] * (len(subsequence) + 1)
    min_score = None
    min_score_idx = None

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

    return (min_score, min_score_idx + 1) if min_score is not None and min_score <= max_l_dist else (None, None)


def _choose_search_range(subseq_len, seq_len, ngram, max_l_dist):
    start_index = max(0, ngram.start - max_l_dist)
    end_index = min(seq_len, seq_len - subseq_len + ngram.end + max_l_dist)
    return start_index, end_index


def find_near_matches_levenshtein_ngrams(subsequence, sequence, max_l_dist):
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
        for index in search_exact(subsequence[ngram.start:ngram.end], sequence, start_index, end_index):
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
