import unittest

from hpman import HyperParameterManager


class TestParse(unittest.TestCase):
    def test_hpm_zoo_import(self):
        from hpman.m import _, __, ___, _____, asdf, asdfkj  # type: ignore

        self.assertIsInstance(_, HyperParameterManager)
        self.assertEqual(_.placeholder, "_")

        self.assertIsInstance(__, HyperParameterManager)
        self.assertEqual(__.placeholder, "__")

        self.assertIsInstance(asdf, HyperParameterManager)
        self.assertEqual(asdf.placeholder, "asdf")

        from hpman.m import _ as t

        self.assertIsInstance(t, HyperParameterManager)
        self.assertEqual(t.placeholder, "_")

        from hpman.m import zzz as xxx

        self.assertIsInstance(xxx, HyperParameterManager)
        self.assertEqual(xxx.placeholder, "zzz")
