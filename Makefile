all:

test:
	mkdir -p test-results
	PY_IGNORE_IMPORTMISMATCH=1 python3 -m pytest \
	    --cov=hpman \
	    --no-cov-on-fail \
	    --cov-report=html:test-results/htmlcov \
	    --cov-report term \
	    --doctest-modules \
	    --junitxml=test-results/junit.xml \
	    hpman tests
	python3 -m coverage xml -o test-results/coverage.xml


format:
	autoflake -r -i examples hpman tests
	isort -rc examples hpman tests
	black examples hpman tests

style-check:
	black --diff --check hpman examples tests
	flake8 --ignore E501,E203,F401,W503,W504 --radon-max-cc 13 hpman examples tests
	mypy hpman

serve-coverage-report:
	cd test-results/htmlcov && python3 -m http.server

wheel:
	python3 setup.py sdist bdist_wheel

doc:
	cd docs && ./gendoc.sh

install:
	# install prerequisites
	# TODO:
	#   1. install requirments
	#   2. install pre-commit hook
