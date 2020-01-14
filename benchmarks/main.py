from __future__ import print_function

import textwrap
import timeit
import argparse
from .micro_benchmarks import benchmarks, search_functions


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


def autorange(timer):
    for i in range(10):
        number = 10 ** i
        time_taken = timer.timeit(number)
        if time_taken >= 0.5:
            break
    return number


def main():
    parser = argparse.ArgumentParser(description='Run fuzzysearch benchmarks.')

    parser.add_argument('-r', '--repetitions', type=int, default=3,
                        help='number of times to run the benchmark')
    parser.add_argument('-n', '--number', type=int,
                        help='number of loop iterations to run in each repetition')

    subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_name')

    micro_parser = subparsers.add_parser('micro', help='micro-benchmarks')
    micro_parser.add_argument('search_function', choices=search_functions)
    micro_parser.add_argument('benchmark', choices=benchmarks)

    book_parser = subparsers.add_parser('book', help='search through the text of a long book')
    book_parser.add_argument('substring', type=str, required=True)
    book_parser.add_argument('max_l_dist', type=int, required=True)

    args = parser.parse_args()

    setup = None
    code = None

    if args.subparser_name == 'micro':
        setup = textwrap.dedent('''\
            from benchmarks.micro_benchmarks import get_benchmark, run_benchmark
            search_func, search_args = get_benchmark({search_function!r},
                                                     {benchmark!r})
        ''').format(**args.__dict__)
        code = 'run_benchmark(search_func, search_args)'
    elif args.subparser_name == 'book':
        setup = textwrap.dedent('''\
            from benchmarks.book import search
        ''')
        code = 'search({substring!r}, {max_l_dist!r})'.format(**args.__dict__)

    timer = timeit.Timer(code, setup=setup)
    try:
        if args.number is None:
            args.number = autorange(timer)
        timings = timer.repeat(args.repetitions, args.number)
    except KeyboardInterrupt:
        print('Aborted!')
    except Exception:
        import traceback
        traceback.print_exc()
        return 1
    else:
        print_results(timings, args.number, args.repetitions)

    return 0


if __name__ == '__main__':
    import sys

    sys.exit(main())
