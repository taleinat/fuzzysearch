import random

from fuzzysearch import find_near_matches
from fuzzysearch.levenshtein import \
    find_near_matches_levenshtein_linear_programming
from fuzzysearch.levenshtein_ngram import \
    find_near_matches_levenshtein_ngrams as fnm_levenshtein_ngrams
from fuzzysearch.substitutions_only import \
    find_near_matches_substitutions_ngrams as fnm_substitutions_ngrams, \
    find_near_matches_substitutions_lp, \
    has_near_match_substitutions_ngrams
from fuzzysearch._substitutions_only import \
    substitutions_only_has_near_matches_lp_byteslike, \
    substitutions_only_has_near_matches_ngrams_byteslike
from fuzzysearch.generic_search import \
    find_near_matches_generic_linear_programming, \
    find_near_matches_generic_ngrams, has_near_match_generic_ngrams
from fuzzysearch._generic_search import \
    c_find_near_matches_generic_linear_programming as \
    find_near_matches_generic_linear_programming_cython


def fnm_levenshtein_lp(subsequence, sequence, max_l_dist):
    return list(find_near_matches_levenshtein_linear_programming(
        subsequence, sequence, max_l_dist))

def fnm_substitutions_lp(subsequence, sequence, max_substitutions):
    return list(find_near_matches_substitutions_lp(
        subsequence, sequence, max_substitutions))

def fnm_generic_lp(subsequence, sequence, max_l_dist):
    return list(find_near_matches_generic_linear_programming(
        subsequence, sequence, max_l_dist, max_l_dist, max_l_dist, max_l_dist))

def fnm_generic_lp_cython(subsequence, sequence, max_l_dist):
    return list(find_near_matches_generic_linear_programming_cython(
        subsequence, sequence, max_l_dist, max_l_dist, max_l_dist, max_l_dist))

def fnm_generic_ngrams(subsequence, sequence, max_l_dist):
    return list(find_near_matches_generic_ngrams(
        subsequence, sequence, max_l_dist, max_l_dist, max_l_dist, max_l_dist))

def hnm_generic_ngrams(subsequence, sequence, max_l_dist):
    return has_near_match_generic_ngrams(
        subsequence, sequence, max_l_dist, max_l_dist, max_l_dist, max_l_dist)

def hnm_substitutions_ngrams(subsequence, sequence, max_substitutions):
    return has_near_match_substitutions_ngrams(
        subsequence, sequence, max_substitutions)

def hnm_substitutions_byteslike(subsequence, sequence, max_substitutions):
    return substitutions_only_has_near_matches_lp_byteslike(
        subsequence, sequence, max_substitutions)

def hnm_substitutions_ngrams_byteslike(subsequence, sequence, max_substitutions):
    return substitutions_only_has_near_matches_ngrams_byteslike(
        subsequence, sequence, max_substitutions)


search_functions = {
    'fnm': find_near_matches,
    'levenshtein_lp': fnm_levenshtein_lp,
    'levenshtein_ngrams': fnm_levenshtein_ngrams,
    'substitutions_lp': fnm_substitutions_lp,
    'substitutions_ngrams': fnm_substitutions_ngrams,
    'generic_lp': fnm_generic_lp,
    'generic_lp_cython': fnm_generic_lp_cython,
    'generic_ngrams': fnm_generic_ngrams,
    'has_match_generic_ngrams': hnm_generic_ngrams,
    'has_match_substitutions_ngrams': hnm_substitutions_ngrams,
    'has_match_substitutions_byteslike': hnm_substitutions_byteslike,
    'has_match_substitutions_ngrams_byteslike': hnm_substitutions_ngrams_byteslike,
}

benchmarks = {
    'dna_no_match': dict(
        subsequence = 'GCTAGCTAGCTA',
        sequence = "ATCG" * (10**3),
        max_dist = 1,
    ),
    'dna_no_match2': dict(
        subsequence = 'ATGATGATG',
        sequence = 'ATCG' * (10**3),
        max_dist = 2,
    ),
    'random_kevin': dict(
        subsequence = ''.join(random.choice('ATCG') for _i in xrange(36)),
        sequence = ''.join(random.choice('ATCG' * 5 + 'N') for _i in xrange(90)),
        max_dist = 3,
    ),
    'random_kevin_partial_match': dict(
        subsequence = 'AAGTCTAGT' + ''.join(random.choice('ATCG') for _i in xrange(36-9)),
        sequence = 'AAGTCTAGT' + ''.join(random.choice('ATCG' * 5 + 'N') for _i in xrange(90-9)),
        max_dist = 3,
    ),
}


def get_benchmark(search_func_name, benchmark_name):
    search_func = search_functions[search_func_name]
    search_args = dict(benchmarks[benchmark_name])

    if search_func in (find_near_matches,):
        search_args['max_l_dist'] = search_args.pop('max_dist')
    elif search_func in (fnm_levenshtein_ngrams, fnm_levenshtein_lp, fnm_generic_lp, fnm_generic_lp_cython, fnm_generic_ngrams, hnm_generic_ngrams):
        search_args['max_l_dist'] = search_args.pop('max_dist')
    elif search_func in (fnm_substitutions_ngrams, fnm_substitutions_lp, hnm_substitutions_ngrams, hnm_substitutions_byteslike, hnm_substitutions_ngrams_byteslike):
        search_args['max_substitutions'] = search_args.pop('max_dist')
    else:
        raise Exception('Unsupported search function: %r' % search_func)

    return search_func, search_args


def run_benchmark(search_func, search_args):
    return search_func(**search_args)
