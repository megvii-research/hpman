from libhpman import _


def func():
    pass


hpx = _("1-hpx", 123)
hpp = _("2-hpp", func())
xxx = _("3-xxx", {"a": 1, "b": 2})
bbb = _("4-bbb", ["a", 1, 4])
ccc = _("5-ccc", ["a", 1, 4])
xxa = _("6-xxa", 1.24)
fff = _("7-fff", 1e-5)
ggg = _("8-ggg", 1 // 2)
hhh = _("9-hhh", print)
