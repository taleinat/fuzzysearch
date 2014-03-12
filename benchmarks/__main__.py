import sys
import timeit

args = sys.argv[1:]
search_func_name, benchmark_name = args

timeit.main(['-s', 'from benchmarks import run_benchmark', 'run_benchmark(%r, %r)' % (search_func_name, benchmark_name)])
