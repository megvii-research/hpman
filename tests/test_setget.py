import unittest

import hpman


class TestSetGet(unittest.TestCase):
    def setUp(self):
        self.hpm = hpman.HyperParameterManager("_")

    def test_set_multiple_hps(self):
        def test_obj():
            pass

        def foo():
            pass

        test_datas = {
            "a": 1,
            "b": 0.3,
            "c": [1, 2, "a"],
            "d": {"a": 1, "b": "2", "c": 3.0},
            "e": "abc",
            "g": test_obj(),
            "h": foo,
            "f": print,
        }
        self.hpm.set_values(test_datas)
        self.hpm.get_values()
        for name, value in test_datas.items():
            self.assertEqual(self.hpm.get_value(name), value)

    def test_get_tree(self):
        test_datas = {
            "a.a": 1,
            "a.ab": [0.4, 5],
            "b.c": "abc",
            "a.b.c": "abcde",
            "a.b.c5": print,
        }

        self.hpm.set_values(test_datas)
        tree = self.hpm.get_tree()
        self.assertDictEqual(
            tree,
            {
                "a": {"a": 1, "ab": [0.4, 5], "b": {"c": "abcde", "c5": print}},
                "b": {"c": "abc"},
            },
        )
        self.hpm.set_value("a", 0.5)
        with self.assertRaises(ValueError):
            self.hpm.get_tree()

    def test_set_tree(self):
        test_tree = {
            "a": {"a": 1, "ab": [0.4, 5], "b": {"c": "abcde", "c5": print}},
            "b": {"c": "abc"},
        }

        test_datas = {
            "a.a": 1,
            "a.ab": [0.4, 5],
            "b.c": "abc",
            "a.b.c": "abcde",
            "a.b.c5": print,
        }

        self.hpm.set_tree(test_tree)
        for name, value in test_datas.items():
            self.assertEqual(self.hpm.get_value(name), value)

    def test_double_set(self):
        double_set_data = [("a", 1), ("a", 2), ("b", 3.0), ("b", "str")]
        try:
            for name, value in double_set_data:
                self.hpm.set_value(name, value)
                self.assertEqual(self.hpm.get_value(name), value)
        except Exception as e:
            self.fail("double set should be allowed: {}".format(e))

    def test_get_with_nonexist_hp(self):
        self.hpm.set_values({"exist_hp": "1"})
        with self.assertRaises(KeyError):
            self.hpm.get_value("nonexist_hp")
