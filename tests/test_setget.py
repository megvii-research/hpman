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

        test_data = {
            "a": 1,
            "b": 0.3,
            "c": [1, 2, "a"],
            "d": {"a": 1, "b": "2", "c": 3.0},
            "e": "abc",
            "g": test_obj(),
            "h": foo,
            "f": print,
        }
        self.hpm.set_values(test_data)
        self.hpm.get_values()
        for name, value in test_data.items():
            self.assertEqual(self.hpm.get_value(name), value)

    def test_get_tree(self):
        test_data = {
            "a.a": 1,
            "a.ab": [0.4, 5],
            "b.c": "abc",
            "a.b.c": "abcde",
            "a.b.c5": print,
        }

        self.hpm.set_values(test_data)
        tree = self.hpm.get_tree()
        self.assertDictEqual(
            tree,
            {
                "a": {"a": 1, "ab": [0.4, 5], "b": {"c": "abcde", "c5": print}},
                "b": {"c": "abc"},
            },
        )

        # A tree compatible value set should work
        self.hpm.set_value("a.d", 123)
        self.hpm.get_tree()

        # A tree incompatible value set should not work
        self.hpm.set_value("a", 0.5)
        with self.assertRaises(ValueError):
            self.hpm.get_tree()

        # check normal get value works correctly
        self.hpm.get_values()

    def test_set_tree(self):
        test_tree = {
            "a": {"a": 1, "ab": [0.4, 5], "b": {"c": "abcde", "c5": print}},
            "b": {"c": "abc"},
        }

        test_data = {
            "a.a": 1,
            "a.ab": [0.4, 5],
            "b.c": "abc",
            "a.b.c": "abcde",
            "a.b.c5": print,
        }

        self.hpm.set_tree(test_tree)
        for name, value in test_data.items():
            self.assertEqual(self.hpm.get_value(name), value)
        self.assertDictEqual(self.hpm.get_tree("a"), test_tree["a"])
        self.assertDictEqual(self.hpm.get_value("a.b"), test_tree["a"]["b"])

        with self.assertRaises(ValueError):
            self.hpm.set_tree({"a": 2})

    def test_confusion(self):
        def get_output_give_input(data):
            hpm = hpman.HyperParameterManager("_")
            hpm.set_values(data)
            return {"values": hpm.get_values(), "tree": hpm.get_tree()}

        test_data = [{"a": {"b": {"c": 1}}}, {"a.b": {"c": 1}}, {"a.b.c": 1}]
        outs = list(map(get_output_give_input, test_data))

        # For the inputs above, trees are equal ...
        for out in outs[1:]:
            self.assertEqual(out["tree"], outs[0]["tree"])

        # ... but their original values are not
        for out in outs[1:]:
            self.assertNotEqual(out["values"], outs[0]["values"])

    def test_dict_val_in_tree(self):
        test_vals = {"a.b": 1, "c": {"d": 2}}
        self.hpm.set_values(test_vals)
        tree = self.hpm.get_tree()
        hpm = hpman.HyperParameterManager("hp")

        hpm.set_tree(tree)
        self.assertEqual(hpm.get_value("c"), test_vals["c"])
        self.assertEqual(hpm.get_value("c.d"), test_vals["c"]["d"])

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
