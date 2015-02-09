from collections import deque, defaultdict
from itertools import islice
from functools import wraps

import six


from fuzzysearch.common import Match, search_exact, \
    count_differences_with_maximum, get_best_match_in_group, group_matches


def _check_arguments(subsequence, sequence, max_substitutions):
    if not subsequence:
        raise ValueError('Given subsequence is empty!')

    if max_substitutions is None or max_substitutions < 0:
        raise ValueError('Maximum number of substitutions must be >= 0!')


def has_near_match_substitutions(subsequence, sequence, max_substitutions):
    _check_arguments(subsequence, sequence, max_substitutions)

    if max_substitutions == 0:
        for start_index in search_exact(subsequence, sequence):
            return True
        return False

    elif len(subsequence) // (max_substitutions + 1) >= 3:
        return has_near_match_substitutions_ngrams(
            subsequence, sequence, max_substitutions,
        )

    else:
        return has_near_match_substitutions_lp(
            subsequence, sequence, max_substitutions,
        )


def find_near_matches_substitutions(subsequence, sequence, max_substitutions):
    """Find near-matches of the subsequence in the sequence.

    This chooses a suitable fuzzy search implementation according to the given
    parameters.

    Returns a list of fuzzysearch.Match objects describing the matching parts
    of the sequence.
    """
    _check_arguments(subsequence, sequence, max_substitutions)

    if max_substitutions == 0:
        return [
            Match(start_index, start_index + len(subsequence), 0)
            for start_index in search_exact(subsequence, sequence)
        ]

    elif len(subsequence) // (max_substitutions + 1) >= 3:
        return find_near_matches_substitutions_ngrams(
            subsequence, sequence, max_substitutions,
        )

    else:
        return find_near_matches_substitutions_lp(
            subsequence, sequence, max_substitutions,
        )


def find_near_matches_substitutions_lp(subsequence, sequence,
                                       max_substitutions):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the number of character substitutions must be less than max_substitutions
    * no deletions or insertions are allowed
    """
    _check_arguments(subsequence, sequence, max_substitutions)

    return list(_find_near_matches_substitutions_lp(subsequence, sequence,
                                                    max_substitutions))


def _find_near_matches_substitutions_lp(subsequence, sequence,
                                        max_substitutions):
    # simple optimization: prepare some often used things in advance
    _SUBSEQ_LEN = len(subsequence)
    _SUBSEQ_LEN_MINUS_ONE = _SUBSEQ_LEN - 1

    # prepare quick lookup of where a character appears in the subsequence
    char_indexes_in_subsequence = defaultdict(list)
    for (index, char) in enumerate(subsequence):
        char_indexes_in_subsequence[char].append(index)

    # we'll iterate over the sequence once, but the iteration is split into two
    # for loops; therefore we prepare an iterator in advance which will be used
    # in both of the loops
    sequence_enum_iter = enumerate(sequence)

    # We'll count the number of matching characters assuming various attempted
    # alignments of the subsequence to the sequence. At any point in the
    # sequence there will be N such alignments to update. We'll keep
    # these in a "circular array" (a.k.a. a ring) which we'll rotate after each
    # iteration to re-align the indexing.

    # Initialize the candidate counts by iterating over the first N-1 items in
    # the sequence. No possible matches in this step!
    candidates = deque([0], maxlen=_SUBSEQ_LEN)
    for (index, char) in islice(sequence_enum_iter, _SUBSEQ_LEN_MINUS_ONE):
        for subseq_index in [idx for idx in char_indexes_in_subsequence[char] if idx <= index]:
            candidates[subseq_index] += 1
        candidates.appendleft(0)

    # From the N-th item onwards, we'll update the candidate counts exactly as
    # above, and additionally check if the part of the sequence whic began N-1
    # items before the current index was a near enough match to the given
    # sub-sequence.
    for (index, char) in sequence_enum_iter:
        for subseq_index in char_indexes_in_subsequence[char]:
            candidates[subseq_index] += 1

        # rotate the ring of candidate counts
        candidates.rotate(1)
        # fetch the count for the candidate which started N-1 items ago
        n_substitutions = _SUBSEQ_LEN - candidates[0]
        # set the count for the next index to zero
        candidates[0] = 0

        # if the candidate had few enough mismatches, yield a match
        if n_substitutions <= max_substitutions:
            yield Match(
                start=index - _SUBSEQ_LEN_MINUS_ONE,
                end=index + 1,
                dist=n_substitutions,
            )


def has_near_match_substitutions_lp(subsequence, sequence, max_substitutions):
    _check_arguments(subsequence, sequence, max_substitutions)

    for match in _find_near_matches_substitutions_lp(subsequence, sequence,
                                                     max_substitutions):
        return True
    return False


def find_near_matches_substitutions_ngrams(subsequence, sequence,
                                           max_substitutions):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the number of character substitutions must be less than max_substitutions
    * no deletions or insertions are allowed
    """
    _check_arguments(subsequence, sequence, max_substitutions)

    match_starts = set()
    matches = []
    for match in _find_near_matches_substitutions_ngrams(subsequence, sequence,
                                                         max_substitutions):
        if match.start not in match_starts:
            match_starts.add(match.start)
            matches.append(match)
    return sorted(matches, key=lambda match: match.start)


def _find_near_matches_substitutions_ngrams(subsequence, sequence,
                                            max_substitutions):
    subseq_len = len(subsequence)
    seq_len = len(sequence)

    ngram_len = subseq_len // (max_substitutions + 1)
    if ngram_len == 0:
        raise ValueError(
            "The subsequence's length must be greater than max_substitutions!"
        )

    for ngram_start in range(0, len(subsequence) - ngram_len + 1, ngram_len):
        ngram_end = ngram_start + ngram_len
        subseq_before = subsequence[:ngram_start]
        subseq_after = subsequence[ngram_end:]
        for index in search_exact(
                subsequence[ngram_start:ngram_end], sequence,
                ngram_start, seq_len - (subseq_len - ngram_end),
        ):
            n_substitutions = 0
            seq_before = sequence[index - ngram_start:index]
            if subseq_before != seq_before:
                n_substitutions += count_differences_with_maximum(
                    seq_before, subseq_before,
                    max_substitutions - n_substitutions + 1)
                if n_substitutions > max_substitutions:
                    continue

            seq_after = sequence[index + ngram_len:index - ngram_start + subseq_len]
            if subseq_after != seq_after:
                if n_substitutions == max_substitutions:
                    continue
                n_substitutions += count_differences_with_maximum(
                    seq_after, subseq_after,
                    max_substitutions - n_substitutions + 1)
                if n_substitutions > max_substitutions:
                    continue

            yield Match(
                start=index - ngram_start,
                end=index - ngram_start + subseq_len,
                dist=n_substitutions,
            )


def has_near_match_substitutions_ngrams(subsequence, sequence,
                                        max_substitutions):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the number of character substitutions must be less than max_substitutions
    * no deletions or insertions are allowed
    """
    _check_arguments(subsequence, sequence, max_substitutions)

    for match in _find_near_matches_substitutions_ngrams(subsequence, sequence,
                                                         max_substitutions):
        return True
    return False


try:
    from fuzzysearch._substitutions_only import \
        substitutions_only_has_near_matches_ngrams_byteslike, \
        substitutions_only_find_near_matches_ngrams_byteslike as \
            _subs_only_fnm_ngram_byteslike
except ImportError:
    pass
else:
    py_has_near_match_substitutions_ngrams = has_near_match_substitutions_ngrams
    @wraps(py_has_near_match_substitutions_ngrams)
    def has_near_match_substitutions_ngrams(subsequence, sequence,
                                            max_substitutions):
        if not (
            isinstance(subsequence, six.text_type) or
            isinstance(sequence, six.text_type)
        ):
            try:
                return substitutions_only_has_near_matches_ngrams_byteslike(
                    subsequence, sequence, max_substitutions)
            except TypeError:
                pass

        return py_has_near_match_substitutions_ngrams(
            subsequence, sequence, max_substitutions)

    py_find_near_matches_substitutions_ngrams = \
        find_near_matches_substitutions_ngrams
    @wraps(py_find_near_matches_substitutions_ngrams)
    def find_near_matches_substitutions_ngrams(subsequence, sequence,
                                               max_substitutions):
        if not (
            isinstance(subsequence, six.text_type) or
            isinstance(sequence, six.text_type)
        ):
            try:
                results = _subs_only_fnm_ngram_byteslike(
                    subsequence, sequence, max_substitutions)
            except TypeError:
                pass
            else:
                matches = [
                    Match(
                        index,
                        index + len(subsequence),
                        count_differences_with_maximum(
                            sequence[index:index+len(subsequence)],
                            subsequence,
                            max_substitutions + 1,
                        ),
                    )
                    for index in results
                ]
                return [
                    get_best_match_in_group(group)
                    for group in group_matches(matches)
                ]

        return py_find_near_matches_substitutions_ngrams(
            subsequence, sequence, max_substitutions)
