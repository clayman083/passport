.PHONY: all build test clean

clean:
	@rm -rf dist
	@rm -f `find . -type f -name '*.py[co]' `
	@rm -f `find . -type f -name '*~' `
	@rm -f .coverage
	@rm -rf .cache
	@rm -rf .eggs
	@rm -rf coverage
	@rm -rf build
	@rm -rf cover
	@rm -rf .tox

build:
	python setup.py sdist

test:
	tox
