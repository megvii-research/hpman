#!/usr/bin/env python3
import argparse
import os

import lib
from hpman.m import _


def main():
    basedir = os.path.dirname(os.path.realpath(__file__))
    _.parse_file(basedir)

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", default=_.get_value("a"), type=int)
    parser.add_argument("-b", default=_.get_value("b"), type=int)
    args = parser.parse_args()

    _.set_value("a", args.a)
    _.set_value("b", args.b)

    print("a = {}".format(_.get_value("a")))
    print("b = {}".format(_.get_value("b")))
    print("lib.add() = {}".format(lib.add()))
    print("lib.mult() = {}".format(lib.mult()))


if __name__ == "__main__":
    main()
