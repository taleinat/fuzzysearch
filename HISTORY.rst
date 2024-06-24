.. :changelog:

History
-------

0.8.0 (????-??-??)
++++++++++++++++++

* Dropped support for Python 2.7, 3.5, 3.6 and 3.7.
* Added support for Python 3.9, 3.10, 3.11 and 3.12.

0.7.3 (2020-06-27)
++++++++++++++++++

* Fixed segmentation faults due to wrong handling of inputs in bytes-like-only
  functions in C extensions.

0.7.2 (2020-05-07)
++++++++++++++++++
* Added PyPy support.
* Several minor bug fixes.

0.7.1 (2020-04-05)
++++++++++++++++++
* Dropped support for Python 3.4.
* Removed deprecation warning with Python 3.8.
* Fixed a couple of nasty bugs.

0.7.0 (2020-01-14)
++++++++++++++++++

* Added ``matched`` attribue to ``Match`` objects containing the matched part
  of the sequence.
* Added support for CPython 3.8. Now supporting CPython 2.7 and 3.4-3.8.

0.6.2 (2019-04-22)
++++++++++++++++++

* Fix calling ``search_exact()`` without passing ``end_index``.
* Fix edge case: max. dist >= sub-sequence length.

0.6.1 (2018-12-08)
++++++++++++++++++

* Fixed some C compiler warnings for the C and Cython modules

0.6.0 (2018-12-07)
++++++++++++++++++

* Dropped support for Python versions 2.6, 3.2 and 3.3
* Added support and testing for Python 3.7
* Optimized the n-grams Levenshtein search for long sub-sequences
* Further optimized the n-grams Levenshtein search
* Cython versions of the optimized parts of the n-grams Levenshtein search

0.5.0 (2017-09-05)
++++++++++++++++++

* Fixed ``search_exact_byteslike()`` to support supplying start and end indexes
* Added support for lists, tuples and other Sequence types to ``search_exact()``
* Fixed a bug where ``find_near_matches()`` could return a wrong ``Match.end``
  with ``max_l_dist=0``
* Added more tests and improved some existing ones.

0.4.0 (2017-07-06)
++++++++++++++++++

* Added support and testing for Python 3.5 and 3.6
* Many small improvements to README, setup.py and CI testing

0.3.0 (2015-02-12)
++++++++++++++++++

* Added C extensions for several search functions as well as internal functions
* Use C extensions if available, or pure-Python implementations otherwise
* setup.py attempts to build C extensions, but installs without if build fails
* Added ``--noexts`` setup.py option to avoid trying to build the C extensions
* Greatly improved testing and coverage

0.2.2 (2014-03-27)
++++++++++++++++++

* Added support for searching through BioPython Seq objects
* Added specialized search function allowing only subsitutions and insertions
* Fixed several bugs

0.2.1 (2014-03-14)
++++++++++++++++++

* Fixed major match grouping bug

0.2.0 (2013-03-13)
++++++++++++++++++

* New utility function ``find_near_matches()`` for easier use
* Additional documentation

0.1.0 (2013-11-12)
++++++++++++++++++

* Two working implementations
* Extensive test suite; all tests passing
* Full support for Python 2.6-2.7 and 3.1-3.3
* Bumped status from Pre-Alpha to Alpha

0.0.1 (2013-11-01)
++++++++++++++++++

* First release on PyPI.