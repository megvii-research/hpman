all:

test:
	nose2 --coverage libhpman -s . \
	    --with-coverage \
	    --plugin nose2.plugins.doctests \
	    --with-doctest \
	    --coverage-report html \
	    --coverage-report term-missing 

serve-coverage-report:
	cd htmlcov && python3 -m http.server

doc:
	# TODO
	
install:  
	# install prerequisites
	# TODO: 
	#   1. install requirments
	#   2. install pre-commit hook
	
