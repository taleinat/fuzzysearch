from fuzzysearch import find_near_matches_customized_levenshtein, find_near_matches_with_ngrams


def custom_search(subsequence, sequence, max_l_dist):
    return list(find_near_matches_customized_levenshtein(subsequence, sequence, max_l_dist))

search_functions = {
    'custom': custom_search,
    'ngrams': find_near_matches_with_ngrams,
}

benchmarks = {
    'dna_no_match': lambda: dict(
        subsequence = 'GCTAGCTAGCTA',
        sequence = '"ATCG" * (10**3)',
        max_l_dist = 1,
    ),
}

def run_benchmark(search_func_name, benchmark_name, **params):
    search_func = search_functions[search_func_name]
    search_args = benchmarks[benchmark_name](**params)
    return search_func(**search_args)
