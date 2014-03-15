from fuzzysearch.levenshtein import \
    find_near_matches_levenshtein_linear_programming
from fuzzysearch.levenshtein_ngram import \
    find_near_matches_levenshtein_ngrams as fnm_levenshtein_ngrams
from fuzzysearch.susbstitutions_only import \
    find_near_matches_substitutions_ngrams as fnm_substitutions_ngrams, \
    find_near_matches_substitutions_linear_programming


def fnm_levenshtein_lp(subsequence, sequence, max_l_dist):
    return list(find_near_matches_levenshtein_linear_programming(
        subsequence, sequence, max_l_dist))

def fnm_substitutions_lp(subsequence, sequence, max_substitutions):
    return list(find_near_matches_substitutions_linear_programming(
        subsequence, sequence, max_substitutions))


search_functions = {
    'levenshtein_lp': fnm_levenshtein_lp,
    'levenshtein_ngrams': fnm_levenshtein_ngrams,
    'substitutions_lp': fnm_substitutions_lp,
    'substitutions_ngrams': fnm_substitutions_ngrams,
}

benchmarks = {
    'dna_no_match': dict(
        subsequence = 'GCTAGCTAGCTA',
        sequence = '"ATCG" * (10**3)',
        max_dist = 1,
    ),
}


def run_benchmark(search_func_name, benchmark_name):
    search_func = search_functions[search_func_name]
    search_args = dict(benchmarks[benchmark_name])

    if search_func in (fnm_levenshtein_ngrams, fnm_levenshtein_lp):
        search_args['max_l_dist'] = search_args.pop('max_dist')
    elif search_func in (fnm_substitutions_ngrams, fnm_substitutions_lp):
        search_args['max_substitutions'] = search_args.pop('max_dist')
    else:
        raise Exception('Unsupported search function: %r' % search_func)

    return search_func(**search_args)
