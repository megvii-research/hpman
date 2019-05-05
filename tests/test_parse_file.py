import unittest
import libhpman
import os


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def f(x):
    return os.path.join(DIR_PATH, x)


class TestParse(unittest.TestCase):
    def _create_hpm(self):
        return libhpman.HyperParameterManager("_")

    def test_parse_file_allinone(self):
        try:
            m = self._create_hpm().parse_file(f("test_files/all_in_one.py"))
        except Exception as e:
            self.assertEqual("parse with error: {}".format(e), "")

        self.assertEqual(len(m.db), 9)

    def test_parse_file_with_combination_of_paths(self):
        m = self._create_hpm().parse_file(f("test_files/1/1.py"))
        self.assertEqual(len(m.db), 9)

        m = self._create_hpm().parse_file(f("test_files/"))
        self.assertEqual(len(m.db), 3 * 9)

        m = self._create_hpm().parse_file(
            list(map(f, ["test_files/1/1.py", "test_files/2/2.py"]))
        )
        self.assertEqual(len(m.db), 2 * 9)

        m = self._create_hpm().parse_file(
            list(map(f, ["test_files/1", "test_files/2"]))
        )
        self.assertEqual(len(m.db), 2 * 9)

    def test_parse_file_with_non_exist_path(self):
        try:
            m = self._create_hpm().parse_file("none_exist_path")
            self.assertEqual(len(m.db), 0)
        except Exception as e:
            self.fail("path not existed cause failure: {}".format(e))

    def test_parse_file_with_not_py_path(self):
        m = self._create_hpm().parse_file(f("test_files/no_py"))
        self.assertEqual(len(m.db), 0)

        m = self._create_hpm().parse_file(f("test_files/no_py/no_py.txt"))
        self.assertEqual(len(m.db), 0)

    def test_parse_file_with_duplicated_paths(self):
        try:
            m = self._create_hpm().parse_file(
                list(map(f, ["test_files/1/1.py", "test_files/1/1.py"]))
            )
            self.assertEqual(len(m.db), 9)
        except Exception as e:
            self.fail("duplication path should be removed: {}".format(e))

        try:
            m = self._create_hpm().parse_file(
                list(map(f, ["test_files/", "test_files/1/1.py"]))
            )
            self.assertEqual(len(m.db), 27)
        except Exception as e:
            self.fail("duplication path should be removed: {}".format(e))
