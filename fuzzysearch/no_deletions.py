"""fuzzy searching allowing subsitutions and insertions, but no deletions"""

__all__ = [
    'find_near_matches_no_deletions_ngrams',
]

import array

from fuzzysearch.common import Ngram, search_exact, Match


def _expand(subsequence, sequence, max_substitutions, max_insertions,
            max_l_dist):
    if not subsequence:
        return (0, 0)

    n_subs = array.array('L', [0] * (max_insertions + 1))
    for subseq_index, char in enumerate(subsequence):
        n_subs[0] += (char != sequence[subseq_index])
        for n_ins in range(1, max_insertions + 1):
            n_subs[n_ins] = min(
                n_subs[n_ins] + (char != sequence[subseq_index + n_ins]),
                n_subs[n_ins - 1]
            )

    matches = [
        (_n_subs, _n_ins) for (_n_ins, _n_subs) in enumerate(n_subs)
        if _n_subs <= max_substitutions
        and _n_ins + _n_subs <= max_l_dist
    ]
    return [
        match for (i, match) in enumerate(matches)
        if i == 0 or match[0] < matches[i-1][0]
    ]


def find_near_matches_no_deletions_ngrams(subsequence, sequence,
                                          max_substitutions, max_insertions,
                                          max_l_dist=None):
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

    if max_l_dist is None or max_l_dist > max_substitutions + max_insertions:
        max_l_dist = max_substitutions + max_insertions
    max_substitutions = min(max_substitutions, max_l_dist)
    max_insertions = min(max_insertions, max_l_dist)

    ngram_len = _SUBSEQ_LEN // (max_substitutions + max_insertions + 1)
    if ngram_len == 0:
        raise ValueError(
            "The subsequence's length must be greater than max_subs + max_ins!"
        )

    ngrams = [
        Ngram(start, start + ngram_len)
        for start in range(0, len(subsequence) - ngram_len + 1, ngram_len)
    ]
    matches = []
    matched_indexes = set()

    for ngram in ngrams:
        _subseq_before = subsequence[:ngram.start]
        _subseq_before_reversed = _subseq_before[::-1]
        _subseq_after = subsequence[ngram.end:]
        start_index = max(0, ngram.start - max_insertions)
        end_index = min(_SEQ_LEN, _SEQ_LEN - (_SUBSEQ_LEN - ngram.end) + max_insertions)

        for index in search_exact(subsequence[ngram.start:ngram.end], sequence, start_index, end_index):
            if index - ngram.start in matched_indexes:
                continue

            seq_after = sequence[index + ngram_len:index + _SUBSEQ_LEN - ngram.start + max_insertions]
            if seq_after.startswith(_subseq_after):
                matches_after = [(0, 0)]
            else:
                matches_after = _expand(_subseq_after, seq_after,
                                  max_substitutions, max_insertions, max_l_dist)
                if not matches_after:
                    continue

            _max_substitutions = max_substitutions - min(m[0] for m in matches_after)
            _max_insertions = max_insertions - min(m[1] for m in matches_after)
            _max_l_dist = max_l_dist - min(m[0] + m[1] for m in matches_after)
            seq_before = sequence[index - ngram.start - _max_insertions:index]
            if seq_before.endswith(_subseq_before):
                matches_before = [(0, 0)]
            else:
                matches_before = _expand(
                    _subseq_before_reversed, seq_before[::-1],
                    _max_substitutions, _max_insertions, _max_l_dist,
                )

            for (subs_before, ins_before) in matches_before:
                for (subs_after, ins_after) in matches_after:
                    if (
                            subs_before + subs_after <= max_substitutions and
                            ins_before + ins_after <= max_insertions and
                            subs_before + subs_after + ins_before + ins_after <= max_l_dist
                    ):
                        matches.append(Match(
                            start=index - ngram.start - ins_before,
                            end=index - ngram.start + _SUBSEQ_LEN + ins_after,
                            dist=subs_before + subs_after + ins_before + ins_after,
                        ))
                        matched_indexes |= set(range(
                            index - ngram.start - ins_before,
                            index - ngram.start - ins_before + max_insertions + 1,
                        ))

    return sorted(matches, key=lambda match: match.start)
