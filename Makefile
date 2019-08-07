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
	autoflake -r -i examples hpman tests
	isort -rc examples hpman tests
	black examples hpman tests

style-check:
	black --diff --check hpman examples tests
	flake8 --ignore E501,E203,F401,W503,W504 --radon-max-cc 13 hpman examples tests 
	mypy hpman 

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
	
