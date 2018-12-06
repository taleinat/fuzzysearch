from fuzzysearch.common import Match, \
    group_matches, get_best_match_in_group, search_exact

from six.moves import xrange


__all__ = ['find_near_matches_levenshtein_ngrams']


def _expand(subsequence, sequence, max_l_dist):
    """Expand a partial match of a Levenstein search.

    An expansion must begin at the beginning of the sequence, which makes
    this much simpler than a full search, and allows for greater optimization.
    """
    if not subsequence:
        return (0, 0)

    # If given a long sub-sequence and relatively small max distance,
    # use a more complex algorithm better optimized for such cases.
    if len(subsequence) > max(max_l_dist * 2, 10):
        return _expand_long(subsequence, sequence, max_l_dist)
    else:
        return _expand_short(subsequence, sequence, max_l_dist)


def _expand_short(subsequence, sequence, max_l_dist):
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

    subseq_len = len(subsequence)

    scores = list(range(1, subseq_len + 1))
    min_score = subseq_len
    min_score_idx = 0

    for seq_index, char in enumerate(sequence):
        a = seq_index
        c = a + 1
        for subseq_index in range(subseq_len):
            b = scores[subseq_index]
            c = scores[subseq_index] = min(
                a + (char != subsequence[subseq_index]),
                b + 1,
                c + 1,
            )
            a = b
        if c <= min_score:
            min_score = c
            min_score_idx = seq_index

    return (min_score, min_score_idx + 1) if min_score <= max_l_dist else (None, None)


# def _expand_long_sequence(subsequence, sequence, max_l_dist):
#     """Partial match expansion optimized for long sub-sequences."""
#     subseq_len = len(subsequence)
#
#     scores = list(range(subseq_len + 1))
#     new_scores = [None] * (subseq_len + 1)
#     min_score = None
#     min_score_idx = None
#
#     for seq_index, char in enumerate(sequence):
#         new_scores[0] = scores[0] + 1
#         min_intermediate_score = new_scores[0]
#         for subseq_index in range(0, min(seq_index + max_l_dist, subseq_len-1)):
#             new_scores[subseq_index + 1] = min(
#                 scores[subseq_index] + (0 if char == subsequence[subseq_index] else 1),
#                 scores[subseq_index + 1] + 1,
#                 new_scores[subseq_index] + 1,
#             )
#         subseq_index = min(seq_index + max_l_dist, subseq_len - 1)
#         new_scores[subseq_index + 1] = last_score = min(
#             scores[subseq_index] + (0 if char == subsequence[subseq_index] else 1),
#             new_scores[subseq_index] + 1,
#         )
#         if subseq_index == subseq_len - 1 and (min_score is None or last_score <= min_score):
#             min_score = last_score
#             min_score_idx = seq_index
#
#         scores, new_scores = new_scores, scores
#
#     return (min_score, min_score_idx + 1) if min_score is not None and min_score <= max_l_dist else (None, None)


# def _expand_long_subsequence(subsequence, sequence, max_l_dist):
def _expand_long(subsequence, sequence, max_l_dist):
    """Partial match expansion optimized for long sub-sequences."""
    # The additional optimization in this version is to limit the part of
    # the sub-sequence inspected for each sequence character.  The start and
    # end of the iteration are limited to the range where the scores are
    # smaller than the maximum distance.
    subseq_len = len(subsequence)

    scores = list(range(subseq_len + 1))
    new_scores = [None] * (subseq_len + 1)

    min_score = None
    min_score_idx = None
    max_good_score = max_l_dist
    first_good_score_idx = 0
    last_good_score_idx = subseq_len - 1

    for seq_index, char in enumerate(sequence):
        needle_idx_range = (
            max(0, first_good_score_idx - 1),
            min(subseq_len - 1, last_good_score_idx),
        )

        new_scores[0] = scores[0] + 1
        if new_scores[0] <= max_good_score:
            first_good_score_idx = 0
            last_good_score_idx = 0
        else:
            first_good_score_idx = None
            last_good_score_idx = -1

        for subseq_index in range(*needle_idx_range):
            score = new_scores[subseq_index + 1] = min(
                scores[subseq_index] + (0 if char == subsequence[subseq_index] else 1),
                scores[subseq_index + 1] + 1,
                new_scores[subseq_index] + 1,
            )
            if score <= max_good_score:
                if first_good_score_idx is None:
                    first_good_score_idx = subseq_index + 1
                last_good_score_idx = max(
                    last_good_score_idx,
                    subseq_index + 1 + (max_good_score - score),
                )

        subseq_index = needle_idx_range[1]
        new_scores[subseq_index + 1] = last_score = min(
            scores[subseq_index] + (0 if char == subsequence[subseq_index] else 1),
            new_scores[subseq_index] + 1,
        )
        if last_score <= max_good_score:
            if first_good_score_idx is None:
                first_good_score_idx = subseq_index + 1
            last_good_score_idx = subseq_index + 1

        if first_good_score_idx is None:
            break

        if subseq_index == subseq_len - 1 and (min_score is None or last_score <= min_score):
            min_score = last_score
            min_score_idx = seq_index
            if min_score < max_good_score:
                max_good_score = min_score

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
