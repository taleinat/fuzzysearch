import sys
import timeit

args = sys.argv[1:]
search_func_name, benchmark_name = args

timeit.main(['-s', 'from benchmarks import get_benchmark, run_benchmark; search_func, search_args = get_benchmark(%r, %r)' % (search_func_name, benchmark_name), 'run_benchmark(search_func, search_args)'])
