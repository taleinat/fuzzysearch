.. :changelog:

History
-------

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