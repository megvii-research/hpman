#!/bin/bash
# use local version instead of installed version
export PYTHONPATH="$(pwd)/..:$PYTHONPATH"

set -x
sphinx-apidoc -f -o api ../hpman
make SPHINXOPTS="-n" html
