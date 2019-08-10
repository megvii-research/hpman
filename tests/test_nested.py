#!/usr/bin/env python
import unittest

import hpman
from hpman.primitives import ImpossibleTree


class TestNestedParams(unittest.TestCase):
    def setUp(self):
        self.hpm = hpman.HyperParameterManager("_")

    def test_nested_case1(self):
        expr = "_('a.b', 1)\n" "_('c', {'d': 2})\n" "_('a.b')\n" "_('c.d')"
        with self.assertRaises(ImpossibleTree):
            self.hpm.parse_source(expr)

    def test_nested_case2(self):
        expr = "_('a.b', 1)\n" "_('c', {'d': 2})\n" "_('a.b')\n"
        self.hpm.parse_source(expr)
        with self.assertRaises(KeyError):
            self.hpm("c.d")

        self.assertDictEqual(self.hpm.get_tree(), {"a": {"b": 1}, "c": {"d": 2}})
        self.hpm.set_tree({"c": {"d": 3}})
        self.assertDictEqual(self.hpm.get_tree(), {"a": {"b": 1}, "c": {"d": 3}})
        self.assertDictEqual(self.hpm.get_value("c"), {"d": 3})

    def test_nested_case2_2(self):
        expr = "_('a.b', 1)\n" "_('c', {'d': 2})\n" "_('a.b')\n"
        self.hpm.parse_source(expr)

        self.hpm.set_value("c.d", 3)
        self.assertDictEqual(self.hpm.get_tree(), {"a": {"b": 1}, "c": {"d": 3}})
        self.assertDictEqual(self.hpm.get_value("c"), {"d": 3})

    def test_nested_case3(self):
        expr = "_('a.b', 1)\n" "_('a', {'c': 2})"
        with self.assertRaises(ImpossibleTree):
            self.hpm.parse_source(expr)


# vim: ts=4 sw=4 sts=4 expandtab
