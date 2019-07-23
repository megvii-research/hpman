from hpman import HyperParameterManager

_ = HyperParameterManager("_")


def func():
    pass


hpx = _("10", 123)
xxx = _("20", {"a": 1, "b": 2})
bbb = _("30", ["a", 1, 4])
ccc = _("40", ["a", 1, 4])
xxa = _("50", 1.24)
fff = _("60", 1e-5)
ggg = _("70", 1 // 2)
hhh = _("80", print)
hpp = _("90", func())
