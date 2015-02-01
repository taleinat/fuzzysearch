from fuzzysearch.common import Match, \
    group_matches, get_best_match_in_group, search_exact

from six.moves import xrange


__all__ = ['find_near_matches_levenshtein_ngrams']


def _expand(subsequence, sequence, max_l_dist):
    if not subsequence:
        return (0, 0)

    scores = list(range(max_l_dist + 1)) + [None] * (len(subsequence) + 1 - (max_l_dist + 1))
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


def find_near_matches_levenshtein_ngrams(subsequence, sequence, max_l_dist):
    subseq_len = len(subsequence)
    seq_len = len(sequence)

    ngram_len = subseq_len // (max_l_dist + 1)
    if ngram_len == 0:
        raise ValueError('the subsequence length must be greater than max_l_dist')

    matches = []
    for ngram_start in xrange(0, subseq_len - ngram_len + 1, ngram_len):
        ngram_end = ngram_start + ngram_len
        subseq_before_reversed = subsequence[:ngram_start][::-1]
        subseq_after = subsequence[ngram_end:]
        start_index = max(0, ngram_start - max_l_dist)
        end_index = min(seq_len, seq_len - subseq_len + ngram_end + max_l_dist)
        for index in search_exact(subsequence[ngram_start:ngram_end], sequence, start_index, end_index):
            # try to expand left and/or right according to n_ngram
            dist_right, right_expand_size = _expand(
                subseq_after,
                sequence[index + ngram_len:index - ngram_start + subseq_len + max_l_dist],
                max_l_dist,
            )
            if dist_right is None:
                continue
            dist_left, left_expand_size = _expand(
                subseq_before_reversed,
                sequence[max(0, index - ngram_start - (max_l_dist - dist_right)):index][::-1],
                max_l_dist - dist_right,
            )
            if dist_left is None:
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
