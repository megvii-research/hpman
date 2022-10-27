import os
import unittest

import hpman

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def f(x):
    return os.path.join(DIR_PATH, x)


class TestParse(unittest.TestCase):
    def _create_hpm(self):
        return hpman.HyperParameterManager("_")

    def test_parse_file_allinone(self):
        try:
            m = self._create_hpm().parse_file(f("test_files/all_in_one.py"))
        except Exception as e:
            self.assertEqual("parse with error: {}".format(e), "")

        self.assertEqual(m.tree.count(), 9)

    def test_parse_file_with_combination_of_paths(self):
        m = self._create_hpm().parse_file(f("test_files/1/1.py"))
        self.assertEqual(m.tree.count(), 9)

        m = self._create_hpm().parse_file(f("test_files/"))
        self.assertEqual(m.tree.count(), 3 * 9)

        m = self._create_hpm().parse_file(
            list(map(f, ["test_files/1/1.py", "test_files/2/2.py"]))
        )
        self.assertEqual(m.tree.count(), 2 * 9)

        m = self._create_hpm().parse_file(
            list(map(f, ["test_files/1", "test_files/2"]))
        )
        self.assertEqual(m.tree.count(), 2 * 9)

    def test_parse_file_with_non_exist_path(self):
        self.assertRaises(
            FileNotFoundError, self._create_hpm().parse_file, "none_exist_path"
        )

    def test_parse_file_with_not_py_path(self):
        m = self._create_hpm().parse_file(f("test_files/no_py"))
        self.assertEqual(m.tree.count(), 0)

        m = self._create_hpm().parse_file(f("test_files/no_py/no_py.txt"))
        self.assertEqual(m.tree.count(), 0)

    def test_parse_file_with_duplicated_paths(self):
        try:
            m = self._create_hpm().parse_file(
                list(map(f, ["test_files/1/1.py", "test_files/1/1.py"]))
            )
            self.assertEqual(m.tree.count(), 9)
        except Exception as e:
            self.fail("duplication path should be removed: {}".format(e))

        try:
            m = self._create_hpm().parse_file(
                list(map(f, ["test_files/", "test_files/1/1.py"]))
            )
            self.assertEqual(m.tree.count(), 27)
        except Exception as e:
            self.fail("duplication path should be removed: {}".format(e))
