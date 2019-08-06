all:

test:
	pytest \
	    --cov=hpman \
	    --no-cov-on-fail \
	    --cov-report=html:htmlcov \
	    --cov-report term \
	    --doctest-modules \
	    hpman tests

format:
	isort -rc hpman tests
	black hpman tests

style-check:
	black --diff --check .

serve-coverage-report:
	cd htmlcov && python3 -m http.server

wheel:
	python3 setup.py sdist bdist_wheel

doc:
	cd docs && ./gendoc.sh

install:  
	# install prerequisites
	# TODO: 
	#   1. install requirments
	#   2. install pre-commit hook
	
