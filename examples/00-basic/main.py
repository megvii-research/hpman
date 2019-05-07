from libhpman.m import _

# forward static parsing
_.parse_file(__file__)
print(_.get_value("learning_rate"))

# define hyper-parameters
learning_rate = _("learning_rate", 1e-3)

# override default value
_.set_value("learning_rate", 1e-2)
print(_.get_value("learning_rate"))
