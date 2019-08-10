import ast
import unittest

import hpman
from hpman.primitives import ImpossibleTree


class TestParseSource(unittest.TestCase):
    # Note: clear is not required since that parse won't
    #   affect the hyperparameters instance in memory

    def setUp(self):
        self.hpm = hpman.HyperParameterManager("_")

    def test_parse_name_with_non_literal_name(self):
        non_literal_name = "hp_name"
        self.assertRaises(
            hpman.NotLiteralNameException,
            self.hpm.parse_source,
            "_({}, {})".format(non_literal_name, 1),
        )

    def test_parse_type_with_pod(self):
        self._run(
            {
                "_('hp_int', 123)": ["hp_int", 123, ast.Num],
                "_('hp_int_hex', 0x18)": ["hp_int_hex", 0x18, ast.Num],
                "_('hp_float', 3.14)": ["hp_float", 3.14, ast.Num],
                "_('hp_float_ieee', 1e-5)": ["hp_float_ieee", 1e-5, ast.Num],
                "_('hp_str', 'string')": ["hp_str", "string", ast.Str],
            }
        )

    def test_parse_hints(self):
        self._run(
            {
                "_('hp0', 1, a=1, b=2, c={'d': 3, 'e': 4})": [
                    "hp0",
                    1,
                    ast.Num,
                    {"a": 1, "b": 2, "c": {"d": 3, "e": 4}},
                ],
                "_('hp1', 1, a=[1, 3, 4], b=2, c={'d': 3, 'e': 4})": [
                    "hp1",
                    1,
                    ast.Num,
                    {"a": [1, 3, 4], "b": 2, "c": {"d": 3, "e": 4}},
                ],
            }
        )

    def test_parse_hints_not_literal_evaluable(self):
        self.assertRaises(
            hpman.NotLiteralEvaluable, self.hpm.parse_source, "a = _('a', 1, type=dict)"
        )

    def test_parse_type_with_list(self):
        self._run(
            {
                "_('hp_list', [1, 'a', 1.24, 1e-5])": [
                    "hp_list",
                    [1, "a", 1.24, 1e-5],
                    ast.List,
                ],
                "_('hp_list_nested', [1, 'a', [1, 'a']])": [
                    "hp_list_nested",
                    [1, "a", [1, "a"]],
                    ast.List,
                ],
            }
        )

    def test_parse_type_with_dict(self):
        self._run(
            {
                "_('hp_dict', {'comp1': 0.12, 'comp2': 2, 'comp3': 'a'})": [
                    "hp_dict",
                    {"comp1": 0.12, "comp2": 2, "comp3": "a"},
                    ast.Dict,
                ],
                "_('hp_dict_nested', {'a': 1, 'b': 1.8, 'c': {1: 'a'}, 'd': [1, 2, 3]})": [
                    "hp_dict_nested",
                    {"a": 1, "b": 1.8, "c": {1: "a"}, "d": [1, 2, 3]},
                    ast.Dict,
                ],
            }
        )

    def test_parse_type_with_func(self):
        self._run(
            {
                "_('hp_func', print)": [
                    "hp_func",
                    hpman.NotLiteralEvaluable(),
                    ast.Name,
                ],
                "_('hp_lambda', lambda x: x)": [
                    "hp_lambda",
                    hpman.NotLiteralEvaluable(),
                    ast.Lambda,
                ],
                "def foo():\n"
                "    pass\n"
                "_('hp_def', foo)": ["hp_def", hpman.NotLiteralEvaluable(), ast.Name],
                "_('hp_call', bytes('abc'))": [
                    "hp_call",
                    hpman.NotLiteralEvaluable(),
                    ast.Call,
                ],
            }
        )

    def test_parse_type_with_obj(self):
        self._run(
            {
                "class Test:\n"
                "   pass\n"
                "obj = Test()\n"
                "_('hp_obj', obj)": ["hp_obj", hpman.NotLiteralEvaluable(), ast.Name]
            }
        )

    def test_parse_normal_multi_assignment(self):
        self.hpm.parse_source("_('hp1', 1)\n" "_('hp2', 2)")

    def test_parse_assign_withvalue_and_novalue(self):
        m = self.hpm.parse_source("_('hp1', 1)\n" "_('hp1')")
        self.assertEqual(m.get_value("hp1"), 1)

        m = self.hpm.parse_source("_('hp2')\n" "_('hp2', 2)")
        self.assertEqual(m.get_value("hp2"), 2)

    def test_parse_double_assignment(self):
        self.assertRaises(
            hpman.DoubleAssignmentException,
            self.hpm.parse_source,
            "_('hp1', 1)\n" "_('hp1', 1)",
        )

        self.assertRaises(
            hpman.DoubleAssignmentException,
            self.hpm.parse_source,
            "_('hp2', 1)\n" "_('hp2', 2)",
        )

    def test_parse_double_assignment_in_different_file(self):
        self.hpm.parse_source("_('hp1', 1)")
        self.assertRaises(
            hpman.DoubleAssignmentException, self.hpm.parse_source, "_('hp1', 1)"
        )

        self.hpm.parse_source("_('hp2', 1)")
        self.assertRaisesRegex(
            hpman.DoubleAssignmentException,
            "Duplicated default values:\n"
            "First occurrence:\n"
            "<unknown>:1\n"
            "==> 1: _\\('hp2', 1\\)\n"
            "Second occurrence:\n"
            "<unknown>:1\n"
            "==> 1: _\\('hp2', 2\\)\n",
            self.hpm.parse_source,
            "_('hp2', 2)",
        )

    def test_parse_underscore_without_value(self):
        m = self.hpm.parse_source("_('hp1')\n" "_('hp2')")
        self.assertIsInstance(
            m.get_value("hp1", raise_exception=False), hpman.EmptyValue
        )
        self.assertIsInstance(
            m.get_value("hp2", raise_exception=False), hpman.EmptyValue
        )

    def test_parse_underscore_with_multi_args(self):
        self.assertRaises(Exception, self.hpm.parse_source, "_('hp', 1, 2)")

    def test_parse_no_underscores(self):
        m = self.hpm.parse_source("abc")
        self.assertTrue(m.tree.empty)

    def test_parse_underscore_along_with_spaces(self):
        m = self.hpm.parse_source("_  ('hp' , 1) ")
        self.assertEqual(m.get_value("hp"), 1)

    def test_parse_underscore_underscore(self):
        m = self.hpm.parse_source("__('hp' , 1) ")
        self.assertTrue(m.tree.empty)

    def _run(self, test_data):
        """test_data spec:
            {
                '_(key, value)': [
                    key, value
                ],
                ...
            }
        """
        for expression, kv in test_data.items():
            name = kv[0]
            value = kv[1]
            ast_node_type = kv[2]

            m = self.hpm.parse_source(expression)
            # check default value
            if isinstance(value, hpman.NotLiteralEvaluable):
                self.assertEqual(type(m.get_value(name)), hpman.NotLiteralEvaluable)
            else:
                self.assertEqual(m.get_value(name), value)

            # check ast node type
            self.assertEqual(type(m.get_occurrence(name).ast_node), ast_node_type)

            # check hints
            if len(kv) >= 4:
                hints = kv[3]
                parsed_hints = m.get_occurrence(name).hints
                self.assertDictEqual(parsed_hints, hints)

    def test_exists(self):
        self.hpm.parse_source(
            "_('a', 2, type={1: 2, 3: 5})\n" "_('b', 4, sth='good')\n"
        )
        self.hpm.set_values({"b": 1, "c": 2})
        self.assertTrue(self.hpm.exists("a"))
        self.assertTrue(self.hpm.exists("b"))
        self.assertTrue(self.hpm.exists("c"))
        self.assertFalse(self.hpm.exists("d"))
