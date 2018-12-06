from fuzzysearch.common import Match, \
    group_matches, get_best_match_in_group, search_exact

from six.moves import xrange


__all__ = ['find_near_matches_levenshtein_ngrams']


def _expand(subsequence, sequence, max_l_dist):
    """Expand a partial match of a Levenstein search.

    An expansion must begin at the beginning of the sequence, which makes
    this much simpler than a full search, and allows for greater optimization.
    """
    # If given a long sub-sequence and relatively small max distance,
    # use a more complex algorithm better optimized for such cases.
    if len(subsequence) > max(max_l_dist * 2, 10):
        return _expand_long(subsequence, sequence, max_l_dist)
    else:
        return _expand_short(subsequence, sequence, max_l_dist)


def _py_expand_short(subsequence, sequence, max_l_dist):
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
    if subseq_len == 0:
        return (0, 0)

    # Initialize the scores array with values for just skipping sub-sequence
    # chars.
    scores = list(range(1, subseq_len + 1))

    min_score = subseq_len
    min_score_idx = -1

    for seq_index, char in enumerate(sequence):
        # calculate scores, one for each character in the sub-sequence
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

        # keep the minimum score found for matches of the entire sub-sequence
        if c <= min_score:
            min_score = c
            min_score_idx = seq_index

        # bail early when it is impossible to find a better expansion
        elif min(scores) >= min_score:
            break

    return (min_score, min_score_idx + 1) if min_score <= max_l_dist else (None, None)


def _py_expand_long(subsequence, sequence, max_l_dist):
    """Partial match expansion, optimized for long sub-sequences."""
    # The additional optimization in this version is to limit the part of
    # the sub-sequence inspected for each sequence character.  The start and
    # end of the iteration are limited to the range where the scores are
    # smaller than the maximum allowed distance.  Additionally, once a good
    # expansion has been found, the range is further reduced to where the
    # scores are smaller than the score of the best expansion found so far.

    subseq_len = len(subsequence)
    if subseq_len == 0:
        return (0, 0)

    # Initialize the scores array with values for just skipping sub-sequence
    # chars.
    scores = list(range(1, subseq_len + 1))

    min_score = subseq_len
    min_score_idx = -1
    max_good_score = max_l_dist
    new_needle_idx_range_start = 0
    new_needle_idx_range_end = subseq_len - 1

    for seq_index, char in enumerate(sequence):
        # calculate scores, one for each character in the sub-sequence
        needle_idx_range_start = new_needle_idx_range_start
        needle_idx_range_end = min(subseq_len, new_needle_idx_range_end + 1)

        a = seq_index
        c = a + 1

        if c <= max_good_score:
            new_needle_idx_range_start = 0
            new_needle_idx_range_end = 0
        else:
            new_needle_idx_range_start = None
            new_needle_idx_range_end = -1

        for subseq_index in range(needle_idx_range_start, needle_idx_range_end):
            b = scores[subseq_index]
            c = scores[subseq_index] = min(
                a + (char != subsequence[subseq_index]),
                b + 1,
                c + 1,
            )
            a = b

            if c <= max_good_score:
                if new_needle_idx_range_start is None:
                    new_needle_idx_range_start = subseq_index
                new_needle_idx_range_end = max(
                    new_needle_idx_range_end,
                    subseq_index + 1 + (max_good_score - c),
                )

        # bail early when it is impossible to find a better expansion
        if new_needle_idx_range_start is None:
            break

        # keep the minimum score found for matches of the entire sub-sequence
        if needle_idx_range_end == subseq_len and c <= min_score:
            min_score = c
            min_score_idx = seq_index
            if min_score < max_good_score:
                max_good_score = min_score

    return (min_score, min_score_idx + 1) if min_score <= max_l_dist else (None, None)


try:
    from fuzzysearch._levenshtein_ngrams import (
        c_expand_short as _c_expand_short,
        c_expand_long as _c_expand_long,
    )
except ImportError:
    _expand_short = _py_expand_short
    _expand_long = _py_expand_long
else:
    _expand_short = _c_expand_short
    _expand_long = _c_expand_long


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
