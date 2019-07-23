import unittest
from hpman import SourceHelper


import os


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def f(x):
    return os.path.join(DIR_PATH, x)


class TestSourceHelper(unittest.TestCase):
    def test_source_helper_creation(self):
        SourceHelper("a=1\nb=2\n")
        SourceHelper.from_file(f("test_files/all_in_one.py"))

    def test_source_helper_formatters(self):
        sh = SourceHelper("a=1\nc=123\n")
        SourceHelper.format_given_source_and_lineno("a=1", 1)
        SourceHelper.format_given_filepath_and_lineno(f("test_files/all_in_one.py"), 2)
