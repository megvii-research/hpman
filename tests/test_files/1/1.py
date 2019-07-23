from hpman import HyperParameterManager

_ = HyperParameterManager("_")


def func():
    pass


hpx = _("1", 123)
xxx = _("2", {"a": 1, "b": 2})
bbb = _("3", ["a", 1, 4])
ccc = _("4", ["a", 1, 4])
xxa = _("5", 1.24)
fff = _("6", 1e-5)
ggg = _("7", 1 // 2)
hhh = _("8", print)
hpp = _("9", func())

_.parse_file(["tests/test_files/1/", "tests/test_files/1/1.py"])
