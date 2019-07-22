all:

test:
	pytest \
	    --cov=libhpman \
	    --no-cov-on-fail \
	    --cov-report=html:htmlcov \
	    --cov-report term \
	    --doctest-modules \
	    libhpman tests

style-check:
	black --diff --check .

serve-coverage-report:
	cd htmlcov && python3 -m http.server

doc:
	# TODO
	
install:  
	# install prerequisites
	# TODO: 
	#   1. install requirments
	#   2. install pre-commit hook
	
