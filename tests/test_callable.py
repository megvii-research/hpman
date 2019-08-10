import unittest

import hpman


class TestCallable(unittest.TestCase):
    def setUp(self):
        self.hpm = hpman.HyperParameterManager("_")

    def test_assign_without_literal_name(self):
        non_literal_name = "name"
        _ = self.hpm
        try:
            a = _(non_literal_name, 1)
            self.assertEqual(a, 1)
            self.assertEqual(_(non_literal_name), 1)
            self.assertEqual(self.hpm.get_value(non_literal_name), 1)
        except Exception as e:
            self.fail("literal name can not be checked during rumetime: {}".format(e))

    def test_assign_with_all_types(self):
        class test_obj:
            pass

        class test_func:
            pass

        test_data = [
            1,
            3.14,
            1e-5,
            "abc",
            {"a": 1, "b": 2},
            ["a", 1, 4],
            1 // 2,
            print,
            test_obj(),
            test_func,
        ]

        for value in test_data:
            _ = hpman.HyperParameterManager("_")

            a = _("a", value)
            self.assertEqual(a, value)
            self.assertEqual(_("a"), value)
            self.assertEqual(_.get_value("a"), value)

    def test_assign_then_set(self):
        _ = self.hpm
        a = _("a", 1)
        self.assertEqual(a, 1)
        self.assertEqual(_("a"), 1)
        self.assertEqual(self.hpm.get_value("a"), 1)

        _.set_value("a", 2)
        self.assertEqual(_("a"), 2)
        self.assertEqual(_.get_value("a"), 2)

    def test_set_then_assign(self):
        _ = self.hpm
        _.set_value("a", 11)
        self.assertEqual(_("a"), 11)
        self.assertEqual(_.get_value("a"), 11)

        a = _("a", 22)
        # Note: since external-set already, default won't be applied
        self.assertEqual(a, 11)
        self.assertEqual(_("a"), 11)
        self.assertEqual(_.get_value("a"), 11)

    def test_no_value(self):
        _ = self.hpm
        with self.assertRaises(KeyError):
            _("no_value")

    def test_double_assignment_by_setter(self):
        _ = self.hpm
        self.assertEqual(_("a", 2), 2)
        self.assertEqual(_("a", 2), 2)
        self.assertEqual(_("a", 3), 3)
