from collections import deque, defaultdict
from itertools import islice, chain

from fuzzysearch.common import Match, Ngram, search_exact


def find_near_matches_substitutions(subsequence, sequence, max_substitutions):
    """Find near-matches of the subsequence in the sequence.

    This chooses a suitable fuzzy search implementation according to the given
    parameters.

    Returns a list of fuzzysearch.Match objects describing the matching parts
    of the sequence.
    """
    if not subsequence:
        raise ValueError('Given subsequence is empty!')
    if max_substitutions < 0:
        raise ValueError('Maximum number of substitutions must be >= 0!')

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
        return list(find_near_matches_substitutions_linear_programming(
            subsequence, sequence, max_substitutions,
        ))


def find_near_matches_substitutions_linear_programming(subsequence,
                                                       sequence,
                                                       max_substitutions):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the number of character substitutions must be less than max_substitutions
    * no deletions or insertions are allowed
    """
    if not subsequence:
        raise ValueError('Given subsequence is empty!')

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


def find_near_matches_substitutions_ngrams(subsequence, sequence,
                                           max_substitutions):
    """search for near-matches of subsequence in sequence

    This searches for near-matches, where the nearly-matching parts of the
    sequence must meet the following limitations (relative to the subsequence):

    * the number of character substitutions must be less than max_substitutions
    * no deletions or insertions are allowed
    """
    if not subsequence:
        raise ValueError('Given subsequence is empty!')

    _SUBSEQ_LEN = len(subsequence)
    _SEQ_LEN = len(sequence)

    ngram_len = _SUBSEQ_LEN // (max_substitutions + 1)
    if ngram_len == 0:
        raise ValueError(
            "The subsequence's length must be greater than max_substitutions!"
        )

    ngrams = [
        Ngram(start, start + ngram_len)
        for start in range(0, len(subsequence) - ngram_len + 1, ngram_len)
    ]

    matches = []
    match_starts = set()
    for ngram in ngrams:
        _subseq_before = subsequence[:ngram.start]
        _subseq_after = subsequence[ngram.end:]
        start_index = ngram.start
        end_index = _SEQ_LEN - (_SUBSEQ_LEN - ngram.end)
        for index in search_exact(subsequence[ngram.start:ngram.end], sequence, start_index, end_index):
            if (index - ngram.start) in match_starts:
                continue

            n_substitutions = sum((a != b) for (a, b) in chain(
                zip(sequence[index - ngram.start:index], _subseq_before),
                zip(sequence[index + ngram_len:index - ngram.start + _SUBSEQ_LEN], _subseq_after),
            ))

            if n_substitutions <= max_substitutions:
                matches.append(Match(
                    start=index - ngram.start,
                    end=index - ngram.start + _SUBSEQ_LEN,
                    dist=n_substitutions,
                ))
                match_starts.add(index - ngram.start)

    return sorted(matches, key=lambda match: match.start)
