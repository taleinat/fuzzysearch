import timeit

print timeit.timeit(
    'find_near_matches(pattern, text, 1)',
    setup='text = "ATCG" * (10**3); pattern = "GCTAGCTAGCTA"; from fuzzysearch import find_near_matches_with_ngrams as find_near_matches',
)
