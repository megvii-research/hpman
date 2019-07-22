![libhpman logo](assets/libhpman-logo.png)

---

# libhpman (超参侠): hyper parameters under control

**libhpman** is a hyper-parameter manager(HPM) library that truly make sense.
It enables a Distributed-Centralized HPM experience in deep learning
experiment. You can define hyper-parameters anywhere, but manage them as a
whole.

# Example

`lib.py`:
```python
# File: lib.py
from libhpman.m import _


def add():
    return _("a", 0) + _("b", 0)


def mult():
    return _("a") * _("b")
```

`main.py`:
```python
#!/usr/bin/env python3
import os
import argparse

from libhpman.m import _

import lib


def main():
    basedir = os.path.dirname(os.path.realpath(__file__))
    _.parse_file(basedir)

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", default=_.get_value("a"), type=int)
    parser.add_argument("-b", default=_.get_value("b"), type=int)
    args = parser.parse_args()

    _.set_value("a", args.a)
    _.set_value("b", args.b)

    print("a = {}".format(_.get_value("a")))
    print("b = {}".format(_.get_value("b")))
    print("lib.add() = {}".format(lib.add()))
    print("lib.mult() = {}".format(lib.mult()))


if __name__ == "__main__":
    main()
```

Results:
```bash
$ ./main.py
a = 0
b = 0
lib.add() = 0
lib.mult() = 0

$ ./main.py -a 2 -b 3
a = 2
b = 3
lib.add() = 5
lib.mult() = 6
```

This is the core library designed for data manipulation. You may want use
a better front-end:
- [CLI examples](TODO:link-to-hpcli)
- [Jupyter examples](TODO:link-to-hpjui)
- [VSCode Extension](TODO:link-to-hpcode)


# Installation
```
pip install libhpman
```

# Story
Managing ever-changing hyper-parameters is a pain in the a\*\*. During the
practice of training large amount of neural networks, we found two existing
hyper-parameter managing  patterns of the utmost prevalence. 

## Centralized HPM
We call the first type "**centralized HPM**". It follows the way of
configuration management in traditional software, regardless of using a python
file or json or yaml or whatever that can store some key-value mapping (may
remind you of `settings.ini`, `nginx.conf`, etc.):
```python
# File: config.py
BATCH_SIZE = 256
NUM_EPOCH = 120
LEARNING_RATE = 1e-1
WEIGHT_DECAY = 4e-5
OPTIMIZER = 'SGD'
LR_DECAY_EPOCHS = [30, 60, 90]
HIDDEN_CHANNELS = 128
NUM_LAYERS = 5
INPUT_CHANNELS = 784
OUTPUT_CHANNELS = 10 
```

```python
# File: model.py
from torch import nn
import config

def build_model():
    return nn.Sequence(
	[
	    nn.Sequence(nn.Linear(config.INPUT_CHANNELS, config.HIDDEN_CHANNELS), 
			nn.BatchNorm1d(config.HIDDEN_CHANNELS),
			nn.ReLU())
	] + [
	    nn.Sequence(nn.Linear(config.HIDDEN_CHANNELS, config.HIDDEN_CHANNELS), 
			nn.BatchNorm1d(config.HIDDEN_CHANNELS),
			nn.ReLU())
	    for i in range(config.NUM_LAYERS - 1)
	] + [
	    nn.Linear(config.HIDDEN_CHANNELS, config.OUTPUT_CHANNELS)
	]
    )
```
This way of manaing HPs are widely seen in traditional machine learning
libraries, e.g., xgboost, whose HPs are fairly stable compare than that in Deep
Learning. This is good for systematic management of hyper-parameters, acting
as a protocol for tooling.

## However ...
However, it is quite common for researchers to add some additional
parameters at their inspiration (e.g., suddenly come up with a
"Temperature" parameter in softmax.), and alter it often (like number of
channels of a layer), but quickly abandon it if experiments go wrong.
Theses acts are called [Non-Recurring Engineering
(NRE)](https://en.wikipedia.org/wiki/Non-recurring_engineering).

In these cases, the "centralized HPM" reveals obvious drawbacks:
1. Whenever you need to introduce a new HP, you must kind of "declare"
    it in the main configuration file, while using it in some deeply-nested
    easy-to-forget files.
2. Whenever you need to abandon an existing HP, you must not only remove
    all the apearances of that HP in some deeply-nested easy-to-forget
    files, but also remove it in the centralized configuration file.

These drawbacks essentially requires the user to maintain a distributed data
structure, which not only induces great mental burden doing experiments, 
but also be error-prone to bugs.


## Distributed HPM
So researchers come to another solution: forget about config files; define and
use hyper-parameters whenever need, anywhere in the project. We call this
"Distributed HPM".  However, this is hardly called "Management", it more like
anarchism: no management is the best management. This makes starting a new
experiment super delightful: let yourself free and do whatever you want. 

> Let it go, let it go

```python
from torch import nn

def build_model():
    hidden_channels = 128  # <-- hyper-parameter
    return nn.Sequence(
	[
	    nn.Sequence(nn.Linear(784, hidden_channels), # <-- hyper-parameter
			nn.BatchNorm1d(hidden_channels),
			nn.ReLU())
	] + [
	    nn.Sequence(nn.Linear(hidden_channels, hidden_channels), 
			nn.BatchNorm1d(hidden_channels),
			nn.ReLU())
	    for i in range(4)  # <-- hyper-parameter
	] + [
	    nn.Linear(hidden_channels, 10)  # <-- hyper-parameter
	]
    )
```

However, barbaric growth of hyper-parameters of different names in different
places without governance would soon run into a disaster in knowledge sharing,
communication, reproduction, and engineering. Nobody knows what happened, and
nobody knows how to know. You can do nothing, and change nothing.

> You know nothing, John Snow.
>
> 咱也不知道，咱也不敢问呀


## Distributed-Centralized HPM
Now we have two ways of managing hyper-parameters: one is good for engineering
but inconvenient for researchers, another one is convenient for researchers,
but bad for engineering.

We are uncompromising. We did not want to make a decision between these two
choices; we want the best of both worlds.

> 小孩子才做选择，大人全都要

After some trial and error, we came up with a design like this:
```python
from torch import nn
from libhpman.m import _


def build_model():
    hidden_channels = _("hidden_channels", 128)  # <-- hyper-parameter
    return nn.Sequence(
        [
            nn.Sequence(nn.Linear(_("input_channels", 10), hidden_channels),  # <-- hyper-parameter
                        nn.BatchNorm1d(hidden_channels),
                        nn.ReLU())
        ] + [
            nn.Sequence(nn.Linear(hidden_channels, hidden_channels), 
                        nn.BatchNorm1d(hidden_channels),
                        nn.ReLU())
            for i in range(_("num_layers", 5) - 1)  # <-- hyper-parameter
        ] + [
            nn.Linear(hidden_channels, _("output_channels", 10))  # <-- hyper-parameter
        ]
    )
```
and you can auto-magically get all your hyper-parameters like this (prior
actually building the model):
```bash
$ ./train.py --hp-list
All hyperparameters:
    ['hidden_channels', 'input_channels', 'num_layers', 'output_channels']
Details:
+-----------------+--------+---------+-------------------------------------------------------------------------------------------------------------+
| name            | type   |   value | details                                                                                                     |
+=================+========+=========+=============================================================================================================+
| hidden_channels | int    |     128 | occurrence[0]:                                                                                              |
|                 |        |         |   model.py:6                                                                                                |
|                 |        |         |      1: from torch import nn                                                                                |
|                 |        |         |      2: from libhpman.m import _                                                                            |
|                 |        |         |      3:                                                                                                     |
|                 |        |         |      4:                                                                                                     |
|                 |        |         |      5: def build_model():                                                                                  |
|                 |        |         | ==>  6:     hidden_channels = _("hidden_channels", 128)  # <-- hyper-parameter                              |
|                 |        |         |      7:     return nn.Sequence(                                                                             |
|                 |        |         |      8:         [                                                                                           |
|                 |        |         |      9:             nn.Sequence(nn.Linear(_("input_channels", 10), hidden_channels),  # <-- hyper-parameter |
|                 |        |         |     10:                         nn.BatchNorm1d(hidden_channels),                                            |
|                 |        |         |     11:                         nn.ReLU())                                                                  |
+-----------------+--------+---------+-------------------------------------------------------------------------------------------------------------+
| input_channels  | int    |      10 | occurrence[0]:                                                                                              |
|                 |        |         |   model.py:9                                                                                                |
|                 |        |         |      4:                                                                                                     |
|                 |        |         |      5: def build_model():                                                                                  |
|                 |        |         |      6:     hidden_channels = _("hidden_channels", 128)  # <-- hyper-parameter                              |
|                 |        |         |      7:     return nn.Sequence(                                                                             |
|                 |        |         |      8:         [                                                                                           |
|                 |        |         | ==>  9:             nn.Sequence(nn.Linear(_("input_channels", 10), hidden_channels),  # <-- hyper-parameter |
|                 |        |         |     10:                         nn.BatchNorm1d(hidden_channels),                                            |
|                 |        |         |     11:                         nn.ReLU())                                                                  |
|                 |        |         |     12:         ] + [                                                                                       |
|                 |        |         |     13:             nn.Sequence(nn.Linear(hidden_channels, hidden_channels),                                |
|                 |        |         |     14:                         nn.BatchNorm1d(hidden_channels),                                            |
+-----------------+--------+---------+-------------------------------------------------------------------------------------------------------------+
| num_layers      | int    |       5 | occurrence[0]:                                                                                              |
|                 |        |         |   model.py:16                                                                                               |
|                 |        |         |     11:                         nn.ReLU())                                                                  |
|                 |        |         |     12:         ] + [                                                                                       |
|                 |        |         |     13:             nn.Sequence(nn.Linear(hidden_channels, hidden_channels),                                |
|                 |        |         |     14:                         nn.BatchNorm1d(hidden_channels),                                            |
|                 |        |         |     15:                         nn.ReLU())                                                                  |
|                 |        |         | ==> 16:             for i in range(_("num_layers", 5) - 1)  # <-- hyper-parameter                           |
|                 |        |         |     17:         ] + [                                                                                       |
|                 |        |         |     18:             nn.Linear(hidden_channels, _("output_channels", 10))  # <-- hyper-parameter             |
|                 |        |         |     19:         ]                                                                                           |
|                 |        |         |     20:     )                                                                                               |
|                 |        |         |     21:                                                                                                     |
+-----------------+--------+---------+-------------------------------------------------------------------------------------------------------------+
| output_channels | int    |      10 | occurrence[0]:                                                                                              |
|                 |        |         |   model.py:18                                                                                               |
|                 |        |         |     13:             nn.Sequence(nn.Linear(hidden_channels, hidden_channels),                                |
|                 |        |         |     14:                         nn.BatchNorm1d(hidden_channels),                                            |
|                 |        |         |     15:                         nn.ReLU())                                                                  |
|                 |        |         |     16:             for i in range(_("num_layers", 5) - 1)  # <-- hyper-parameter                           |
|                 |        |         |     17:         ] + [                                                                                       |
|                 |        |         | ==> 18:             nn.Linear(hidden_channels, _("output_channels", 10))  # <-- hyper-parameter             |
|                 |        |         |     19:         ]                                                                                           |
|                 |        |         |     20:     )                                                                                               |
|                 |        |         |     21:                                                                                                     |
+-----------------+--------+---------+-------------------------------------------------------------------------------------------------------------+
```
and change the values of these hyper parameters by
```
$ ./train.py -h
usage: train.py [-h] [--hidden-channels HIDDEN_CHANNELS]
                [--output-channels OUTPUT_CHANNELS]
                [--input-channels INPUT_CHANNELS] [--num-layers NUM_LAYERS]
                [--hp-list] [--hp-save HP_SAVE] [--hp-load HP_LOAD]

optional arguments:
  -h, --help            show this help message and exit
  --hidden-channels HIDDEN_CHANNELS
  --output-channels OUTPUT_CHANNELS
  --input-channels INPUT_CHANNELS
  --num-layers NUM_LAYERS
  --hp-list             List all hyperparameters
  --hp-save HP_SAVE     Save hyperparameters to a file. The hyperparameters
                        are saved after processing of all other options
  --hp-load HP_LOAD     Load hyperparameters from a file. The hyperparameters
                        are loaded before any other options are processed
```
(Example are taken from [hpargparse](TODO:link-to-hp-cli))

We are now both **distributed*** (write anywhere) and **centralized** (manage as a whole).

Our design is inspired by the [underscore
function](https://www.gnu.org/software/gettext/manual/html_node/Mark-Keywords.html)
commonly used in [gettext](https://www.gnu.org/software/gettext/) in software
translation. We deem "hyper-parameters" as slots of some text, and different
hyper-parameter values corresponds to different "language" of the same text.

We achieve the above things by parsing your source code statically and extract
where and how you are defining your hyper-parameters. It follows the thoughts
of [Code as Data](https://en.wikipedia.org/wiki/Code_as_data).

Also, expression evaluation in libhpman is quite safe as we are using
`ast.literal_eval`.


# Features
## Define Hyper-Parameters
The most basic (and the most frequently used) function  of libhpman is to
define a hyper-parameter. 
```python
from libhpman.m import _

def training_loop():
    # training settings 
    batch_size = _('batch_size', 128)  # <-- 
```

## Static Parsing
## Runtime Value Getter/Setter
## Aribitrary Imports
## Hints
## Further More

# Development
1. Install requirements:
```
pip install -r requirements.txt
```

2. Install pre-commit hook
```
pre-commit install
```
