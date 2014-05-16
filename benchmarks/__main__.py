import textwrap
import timeit
import argparse
from benchmarks import benchmarks, search_functions


def print_results(timings, number, repeat, precision=3):
    best = min(timings)

    usec = best * 1e6 / number
    if usec < 1000:
        x = "best of %d: %.*g usec per loop" % (repeat, precision, usec)
    else:
        msec = usec / 1000
        if msec < 1000:
            x = "best of %d: %.*g msec per loop" % (repeat, precision, msec)
        else:
            sec = msec / 1000
            x = "best of %d: %.*g sec per loop" % (repeat, precision, sec)

    print("%d loops, " % number + x)


parser = argparse.ArgumentParser(description='Run fuzzysearch benchmarks.')

parser.add_argument('search_function', choices=search_functions)
parser.add_argument('benchmark', choices=benchmarks)
parser.add_argument('-r', '--repetitions', type=int, default=5,
                    help='number of times to run the benchmark')
parser.add_argument('-n', '--number', type=int, default=10**5,
                    help='number of loop iterations to run in each repetition')


args = parser.parse_args()

setup = textwrap.dedent('''\
    from benchmarks import get_benchmark, run_benchmark
    search_func, search_args = get_benchmark({search_function!r},
                                             {benchmark!r})
''').format(**args.__dict__)

code = 'run_benchmark(search_func, search_args)'

timings = timeit.Timer(code, setup=setup).repeat(args.repetitions, args.number)
print_results(timings, args.number, args.repetitions)
