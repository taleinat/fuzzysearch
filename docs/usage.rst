========
Usage
========

To use fuzzysearch in a project:

.. code:: python

	import fuzzysearch

A simple example:

.. code:: python

    >>> find_near_matches('PATTERN', 'aaaPATERNaaa', max_l_dist=1)
    [Match(start=3, end=9, dist=1)]
