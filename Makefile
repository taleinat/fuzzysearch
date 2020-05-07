.PHONY: clean clean-pyc clean-build clean-cython clean-build-ext-inplace lint test coverage docs cython release sdist

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-cython - remove compiled cython files (*.c, *.a, *.o, *.so)"
	@echo "clean - run all of the above clean commands"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "testall - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "cython - compile *.pyx to *.c with cython"
	@echo "release - package and upload a release"
	@echo "sdist - package"

clean: clean-build clean-pyc clean-cython clean-build-ext-inplace

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info
	find src/fuzzysearch -name '*.so' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -type d -name __pycache__ -exec rm -rf {} +

clean-cython:
	find . -name '*.pyx' | sed -n 's/\(.*\/\)*\([^\/]*\)\.pyx$$/\2/p' | xargs -I {} find . \( -name {}.a -o -name {}.o -o -name {}.c -o -name {}.so \) -not -path "./.tox/*" | grep -v '^\./build/' | xargs rm -vf

clean-build-ext-inplace:
	find . -name '*.so' -not -path "./.tox/*" -exec rm {} +

lint:
	flake8 fuzzysearch tests

test:
	tox

coverage:
	test
	coverage report -m
	coverage html
	open htmlcov/index.html

docs:
	rm -f docs/fuzzysearch.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ src/fuzzysearch/
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

src/fuzzysearch/_generic_search.c: src/fuzzysearch/_generic_search.pyx
	cython -2 src/fuzzysearch/_generic_search.pyx

src/fuzzysearch/_levenshtein_ngrams.c: src/fuzzysearch/_levenshtein_ngrams.pyx
	cython -2 src/fuzzysearch/_levenshtein_ngrams.pyx

cython: src/fuzzysearch/_generic_search.c src/fuzzysearch/_levenshtein_ngrams.c

build-ext-inplace: src/fuzzysearch/_generic_search.c src/fuzzysearch/_levenshtein_ngrams.c src/fuzzysearch/_common.c src/fuzzysearch/_substitutions_only.c src/fuzzysearch/wordlen_memmem.c src/fuzzysearch/_substitutions_only_lp_template.h src/fuzzysearch/_substitutions_only_ngrams_template.h
	python setup.py --quiet build_ext --inplace

release: clean
	python setup.py sdist upload

sdist: clean cython
	python setup.py sdist
	ls -l dist
