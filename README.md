# libhpman (超参侠): hyper parameters under control.

----------

**libhpman** is a hyper-parameter manager library that truly make sense. You
can define hyper-parameters anywhere, but manage them as a whole.

```python
from libhpman.m import _

# forward static parsing
_.parse_file(__file__)
print(_.get_value('learning_rate'))

# define hyper-parameters
learning_rate = _('learning_rate', 1e-3)

# override default value
_.set_value('learning_rate', 1e-2)
print(_.get_value('learning_rate'))
```
outputs
```
0.001
0.01
```

# More Examples
[CLI examples](TODO:link-to-libhpman-cli)
[Jupyter examples](TODO:link-to-libhpman-jui-on-mybinder)

# Installation
```
pip install libhpman
```

# Rational
Managing ever-changing hyper-parameters is a pain in the a\*\*.

It is inspired by the [underscore
function](https://www.gnu.org/software/gettext/manual/html_node/Mark-Keywords.html)
commonly used in [gettext](https://www.gnu.org/software/gettext/) in software
translation.

# Features
## Define Hyper-Parameters
## Static Parsing
## Runtime Use
## Aribitrary Imports
## Hints
## Futher

