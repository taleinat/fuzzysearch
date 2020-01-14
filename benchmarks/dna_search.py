from __future__ import print_function

import sys
import textwrap
import timeit


rc = timeit.main(args=(
    '-s', textwrap.dedent('''\
        from fuzzysearch.levenshtein_ngram import \
            find_near_matches_levenshtein_ngrams

        text = "ATCG" * (10**7)
        pattern = "GCTAGCTAGCTA"
        '''),
    'list(find_near_matches_levenshtein_ngrams(pattern, text, 1))',
))

sys.exit(rc)