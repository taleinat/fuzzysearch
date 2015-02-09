============
Installation
============

At the command line::

    $ pip install fuzzysearch

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv fuzzysearch
    $ pip install fuzzysearch

Installation should succeed even if building the C extensions fails. If not,
you can force the installation to skip building the extensions::

    $ pip install fuzzysearch --noexts

