from collections import namedtuple
from fuzzysearch.common import Match, search_exact, \
    group_matches, get_best_match_in_group

import six
from six.moves import xrange


__all__ = [
    'find_near_matches_generic',
    'find_near_matches_generic_linear_programming',
    'find_near_matches_generic_ngrams',
    'has_near_match_generic_ngrams',
]


GenericSearchCandidate = namedtuple(
    'GenericSearchCandidate',
    ['start', 'subseq_index', 'l_dist', 'n_subs', 'n_ins', 'n_dels'],
)


def find_near_matches_generic(subsequence, sequence, search_params):
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

    # if the limitations are so strict that only exact matches are allowed,
    # use search_exact()
    if search_params.max_l_dist == 0:
        return [
            Match(start_index, start_index + len(subsequence), 0)
            for start_index in search_exact(subsequence, sequence)
        ]

    # if the n-gram length would be at least 3, use the n-gram search method
    elif len(subsequence) // (search_params.max_l_dist + 1) >= 3:
        return find_near_matches_generic_ngrams(subsequence, sequence, search_params)

    # use the linear programming search method
    else:
        matches = find_near_matches_generic_linear_programming(subsequence, sequence, search_params)

        match_groups = group_matches(matches)
        best_matches = [get_best_match_in_group(group) for group in match_groups]
        return sorted(best_matches)


def _find_near_matches_generic_linear_programming(subsequence, sequence, search_params):
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

    max_substitutions, max_insertions, max_deletions, max_l_dist = search_params.unpacked

    # optimization: prepare some often used things in advance
    subseq_len = len(subsequence)

    candidates = []
    for index, char in enumerate(sequence):
        candidates.append(GenericSearchCandidate(index, 0, 0, 0, 0, 0))
        new_candidates = []

        for cand in candidates:
            # if this sequence char is the candidate's next expected char
            if char == subsequence[cand.subseq_index]:
                # if reached the end of the subsequence, return a match
                if cand.subseq_index + 1 == subseq_len:
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

                if cand.subseq_index + 1 < subseq_len:
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
                    if cand.subseq_index + n_skipped == subseq_len:
                        yield Match(cand.start, index + 1,
                                    cand.l_dist + n_skipped)
                        break
                    # otherwise, if skipping n_skipped sub-sequence chars
                    # reaches a sub-sequence char identical to this sequence
                    # char ...
                    elif subsequence[cand.subseq_index + n_skipped] == char:
                        # if this is the last char of the sub-sequence, yield
                        # a match
                        if cand.subseq_index + n_skipped + 1 == subseq_len:
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
        n_skipped = subseq_len - cand.subseq_index
        if cand.n_dels + n_skipped <= max_deletions and \
           cand.l_dist + n_skipped <= max_l_dist:
            yield Match(cand.start, index + 1, cand.l_dist + n_skipped)


try:
    from fuzzysearch._generic_search import \
        c_find_near_matches_generic_linear_programming as c_fnm_generic_lp
except ImportError:
    find_near_matches_generic_linear_programming = \
        _find_near_matches_generic_linear_programming
else:
    def find_near_matches_generic_linear_programming(subsequence, sequence, search_params):
        if not (
            isinstance(subsequence, six.text_type) or
            isinstance(sequence, six.text_type)
        ):
            try:
                for match in c_fnm_generic_lp(subsequence, sequence, search_params):
                    yield match
            except TypeError:
                pass

        for match in _find_near_matches_generic_linear_programming(
                subsequence, sequence, search_params):
            yield match


def find_near_matches_generic_ngrams(subsequence, sequence, search_params):
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

    matches = list(_find_near_matches_generic_ngrams(subsequence, sequence, search_params))

    # don't return overlapping matches; instead, group overlapping matches
    # together and return the best match from each group
    match_groups = group_matches(matches)
    best_matches = [get_best_match_in_group(group) for group in match_groups]
    return sorted(best_matches)


def _find_near_matches_generic_ngrams(subsequence, sequence, search_params):
    max_substitutions, max_insertions, max_deletions, max_l_dist = search_params.unpacked

    # optimization: prepare some often used things in advance
    subseq_len = len(subsequence)
    seq_len = len(sequence)

    ngram_len = subseq_len // (max_l_dist + 1)
    if ngram_len == 0:
        raise ValueError('the subsequence length must be greater than max_l_dist')

    for ngram_start in xrange(0, subseq_len - ngram_len + 1, ngram_len):
        ngram_end = ngram_start + ngram_len
        start_index = max(0, ngram_start - max_l_dist)
        end_index = min(seq_len, seq_len - subseq_len + ngram_end + max_l_dist)
        for index in search_exact(subsequence[ngram_start:ngram_end], sequence, start_index, end_index):
            # try to expand left and/or right according to n_ngram
            for match in find_near_matches_generic_linear_programming(
                subsequence, sequence[max(0, index - ngram_start - max_l_dist):index - ngram_start + subseq_len + max_l_dist],
                search_params,
            ):
                yield match._replace(
                    start=match.start + max(0, index - ngram_start - max_l_dist),
                    end=match.end + max(0, index - ngram_start - max_l_dist),
                )


def has_near_match_generic_ngrams(subsequence, sequence, search_params):
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

    for match in _find_near_matches_generic_ngrams(subsequence, sequence, search_params):
        return True
    return False
