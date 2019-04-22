"""Non-naive searching for multiple needles in multiple haystacks."""
from collections import defaultdict

from six.moves import xrange

from fuzzysearch import LevenshteinSearchParams
from fuzzysearch.common import get_best_match_in_group, group_matches
from fuzzysearch.generic_search import find_near_matches_generic_linear_programming


class SequenceNgramIndex(object):
    """An n-gram index of a sequence, for a given n-gram size.

    Once created, this allows for very quick lookup of the indexes where
    any n-gram of the given size appears in the sequence.

    >>> SequenceNgramIndex("-abcde-abcde-", 3).indexes_of_ngram('abc')
    (1, 7)
    """
    def __init__(self, sequence, ngram_size):
        self.sequence = sequence
        self.ngram_size = ngram_size

        self._index = self.index_sequence(self.sequence, self.ngram_size)

    @classmethod
    def index_sequence(cls, sequence, ngram_size):
        index = defaultdict(list)
        for i in range(len(sequence) - ngram_size + 1):
            index[sequence[i:i + ngram_size]].append(i)
        return {
            ngram: tuple(indexes)
            for ngram, indexes in index.items()
        }

    def indexes_of_ngram(self, ngram):
        assert len(ngram) == self.ngram_size
        return self._index.get(ngram, ())


def find_near_matches_multiple(subsequences, sequences,
                               max_substitutions=None,
                               max_insertions=None,
                               max_deletions=None,
                               max_l_dist=None):
    """"Search for near-matches of sub-sequences in sequences.

    This searches for near-matches, where the nearly-matching parts of the
    sequences must meet the following limitations (relative to the
    sub-sequences):

    * the maximum allowed number of character substitutions
    * the maximum allowed number of new characters inserted
    * and the maximum allowed number of character deletions
    * the total number of substitutions, insertions and deletions
      (a.k.a. the Levenshtein distance)

    This returns a list of lists: For each sequence, a list is returned
    of the matches for each sub-sequence within that sequence.

    >>> find_near_matches_multiple(['foo', 'bar'], ['fuo', 'ber'], 1, 1, 1, 1)
    [[[Match(start=0, end=3, dist=1)], []],
     [[], [Match(start=0, end=3, dist=1)]]]
    """
    matches = [[None for _subseq in subsequences] for _seq in sequences]
    if not subsequences:
        return matches

    search_params = LevenshteinSearchParams(
        max_substitutions=max_substitutions,
        max_insertions=max_insertions,
        max_deletions=max_deletions,
        max_l_dist=max_l_dist,
    )
    # note: LevenshteinSearchParams normalizes max_l_dist
    ngram_len = min(map(len, subsequences)) // (search_params.max_l_dist + 1)

    for n_seq, sequence in enumerate(sequences):
        indexed_ngrams = SequenceNgramIndex(sequence, ngram_len)
        for n_subseq, subsequence in enumerate(subsequences):
            matches[n_seq][n_subseq] = \
                search_with_ngram_index(subsequence, sequence,
                                        search_params, indexed_ngrams)

    return matches


def search_with_ngram_index(subsequence, sequence, search_params, indexed_ngrams):
    max_l_dist = search_params.max_l_dist
    ngram_len = indexed_ngrams.ngram_size
    subseq_len = len(subsequence)

    matches = []
    for ngram_start in xrange(0, subseq_len - ngram_len + 1, ngram_len):
        ngram_end = ngram_start + ngram_len
        ngram = subsequence[ngram_start:ngram_end]
        for index in indexed_ngrams.indexes_of_ngram(ngram):
            # try to expand left and/or right according to n_ngram
            for match in find_near_matches_generic_linear_programming(
                    subsequence, sequence[max(0, index - ngram_start - max_l_dist):index - ngram_start + subseq_len + max_l_dist],
                    search_params,
            ):
                matches.append(match._replace(
                    start=match.start + max(0, index - ngram_start - max_l_dist),
                    end=match.end + max(0, index - ngram_start - max_l_dist),
                ))

    # don't return overlapping matches; instead, group overlapping matches
    # together and return the best match from each group
    match_groups = group_matches(matches)
    best_matches = [get_best_match_in_group(group) for group in match_groups]
    return sorted(best_matches)
