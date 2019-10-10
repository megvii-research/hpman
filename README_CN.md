![hpman logo](assets/hpman-logo.png)

---

# hpman (超参侠): 不妥协的超参数管理器。

[![Build Status](https://travis-ci.com/sshao0516/hpman.svg?token=CYoygxuBp4p1Cy7SznNt&branch=master)](https://travis-ci.com/sshao0516/hpman)
[![Docs](https://readthedocs.com/projects/megvii-hpman/badge/?version=latest)](https://megvii-hpman.readthedocs-hosted.com/en/latest/)
[![codecov](https://codecov.io/gh/sshao0516/hpman/branch/master/graph/badge.svg?token=XVeNX2NtUD)](https://codecov.io/gh/sshao0516/hpman)

[English](./README.md) | 简体中文

**hpman** 是一个真正有意义的超参数管理器库。它在深度学习实验中了分布式-集中式超参数管理体验。您可以在任何地方定义超参数，但可以对它们进行整体管理。

hpman旨在作为下游工具的基础构件，例如命令行界面、集成开发环境、实验管理系统等。

hpman支持Python 3.5以上版本。

- [hpman (超参侠): 不妥协的超参数管理器。](#hpman-%e8%b6%85%e5%8f%82%e4%be%a0-%e4%b8%8d%e5%a6%a5%e5%8d%8f%e7%9a%84%e8%b6%85%e5%8f%82%e6%95%b0%e7%ae%a1%e7%90%86%e5%99%a8)
- [背景故事](#%e8%83%8c%e6%99%af%e6%95%85%e4%ba%8b)
  - [集中式超参数管理](#%e9%9b%86%e4%b8%ad%e5%bc%8f%e8%b6%85%e5%8f%82%e6%95%b0%e7%ae%a1%e7%90%86)
  - [然而 ...](#%e7%84%b6%e8%80%8c)
  - [分布式超参数管理](#%e5%88%86%e5%b8%83%e5%bc%8f%e8%b6%85%e5%8f%82%e6%95%b0%e7%ae%a1%e7%90%86)
  - [分布-集中式超参数管理](#%e5%88%86%e5%b8%83-%e9%9b%86%e4%b8%ad%e5%bc%8f%e8%b6%85%e5%8f%82%e6%95%b0%e7%ae%a1%e7%90%86)
- [安装](#%e5%ae%89%e8%a3%85)
- [使用方法](#%e4%bd%bf%e7%94%a8%e6%96%b9%e6%b3%95)
- [样例](#%e6%a0%b7%e4%be%8b)
- [特性](#%e7%89%b9%e6%80%a7)
  - [设计原则](#%e8%ae%be%e8%ae%a1%e5%8e%9f%e5%88%99)
  - [任意名称导入](#%e4%bb%bb%e6%84%8f%e5%90%8d%e7%a7%b0%e5%af%bc%e5%85%a5)
  - [定义超参数](#%e5%ae%9a%e4%b9%89%e8%b6%85%e5%8f%82%e6%95%b0)
  - [静态解析](#%e9%9d%99%e6%80%81%e8%a7%a3%e6%9e%90)
  - [Runtime Value Getter/Setter](#runtime-value-gettersetter)
  - [运行时获取方法和设置方法](#%e8%bf%90%e8%a1%8c%e6%97%b6%e8%8e%b7%e5%8f%96%e6%96%b9%e6%b3%95%e5%92%8c%e8%ae%be%e7%bd%ae%e6%96%b9%e6%b3%95)
  - [提示](#%e6%8f%90%e7%a4%ba)
  - [Nested Hyperparameters](#nested-hyperparameters)
- [Contributing](#contributing)
- [License](#license)

# 背景故事

管理不断变化的超参数是一件头疼的事。
通过进行大量深度学习实验的实践，我们发现了两种最流行的超参数管理模式。

## 集中式超参数管理

我们将第一种方式称之为“**集中式超参数管理**”。它遵循传统软件中的配置管理的方式
，使用python、json或yaml等任何一种可以存储键-值映射的东西（可能使您想起settings.ini，nginx.conf，config.yaml等。）：


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

这种管理超参数的方式在机器学习库（例如xgboost）中得到了广泛的应用，与深度学习研究相比，机器学习的超参数更加稳定。

## 然而 ...

然而，对于研究人员来说，在他们的灵感中添加一些超参数是很普遍的（例如，突然在softmax中提出“温度”参数）。他们可以对超参数进行微调，但是如果实验出错，可以很快放弃。 这些行为称为[一次性工程（NRE）](https://zh.wikipedia.org/wiki/%E4%B8%80%E6%AC%A1%E6%80%A7%E5%B7%A5%E7%A8%8B%E8%B4%B9%E7%94%A8)。

在这种情况下，“集中式超参数管理”显示出明显的缺点：

1. 每当需要引入新的超参数时，都必须在配置文件以某种形式“声明”它，同时在一些深层嵌套的难以记忆的文件中使用它。
2. 每当需要放弃现有的超参数时，不仅必须从一些深层嵌套的难以记忆的文件中删除该超参数的所有体现，而且还必须将其从集中式配置文件中删除。
3. 超参数存在一种“海森堡不确定性”——您无法同时知道超参数是什么和在哪里。使用超参数时，上下文环境传达了该超参数的确切用例的有价值的信息，您需要同时在代码中和集中式配置文件中查找。

这些缺点从根本上要求用户维护分布式数据结构，这不仅在进行实验时会引起很大的心智负担，而且容易出错。

## 分布式超参数管理

因此研究人员提出了另一种解决方案：抛弃配置文件，随时随地在项目中的任何地方定义和使用任何超参数。我们称其为“分布式超参数管理”。事实上，这几乎不能称为“管理”。它更像是无政府主义——没有管理是最好的管理。 这使得添加超参数变得轻松：自由去做自己想做的事情。

> Let it go, let it go

```python
from torch import nn

def build_model():
    hidden_channels = 128  # <-- hyperparameter
    return nn.Sequence(
    [
        nn.Sequence(nn.Linear(784, hidden_channels), # <-- hyperparameter
            nn.BatchNorm1d(hidden_channels),
            nn.ReLU())
    ] + [
        nn.Sequence(nn.Linear(hidden_channels, hidden_channels),
            nn.BatchNorm1d(hidden_channels),
            nn.ReLU())
        for i in range(4)  # <-- hyperparameter
    ] + [
        nn.Linear(hidden_channels, 10)  # <-- hyperparameter
    ]
    )
```

但是，在没有治理的情况下，在不同地方不同名称的超参数的野蛮增长很快将在知识共享、交流、复制和工程设计方面造成灾难。没有人知道发生了什么，什么时候发生，也没有人知道如何轻松地知道。您一无所知，除非您阅读并比较了所有源代码。

> You know nothing, Jon Snow.
>
> 咱也不知道，咱也不敢问呀

## 分布-集中式超参数管理

现在，我们有两种管理超参数的方法：一种对工程有利，但对研究人员不便；另一种对研究人员方便，但对工程不利。

我们毫不妥协。我们不想在这两个选择之间做出决定。我们想要两全其美。

> Only children make choices, adults want them all.
>
> 小孩子才做选择，大人全都要

经过一番反复尝试，我们想到了这样的设计：

`main.py`
```python
#!/usr/bin/env python3

from hpman.m import _
import hpargparse

import argparse


def func():
    weight_decay = _("weight_decay", 1e-5)
    print("weight decay is {}".format(weight_decay))


def main():
    parser = argparse.ArgumentParser()
    _.parse_file(__file__)
    hpargparse.bind(parser, _)
    parser.parse_args()

    func()


if __name__ == "__main__":
    main()
```

同时你可以：

```bash
$ ./main.py
weight decay is 1e-05
$ ./main.py --weight-decay 1e-4
weight decay is 0.0001
$ ./main.py --weight-decay 1e-4 --hp-list
weight_decay: 0.0001
$ ./main.py --weight-decay 1e-4 --hp-list detail
All hyperparameters:
    ['weight_decay']
Details:
+--------------+--------+---------+--------------------------------------------------------------+
| name         | type   |   value | details                                                      |
+==============+========+=========+==============================================================+
| weight_decay | float  |  0.0001 | occurrence[0]:                                               |
|              |        |         |   ./main.py:10                                               |
|              |        |         |      5:                                                      |
|              |        |         |      6: import argparse                                      |
|              |        |         |      7:                                                      |
|              |        |         |      8:                                                      |
|              |        |         |      9: def func():                                          |
|              |        |         | ==> 10:     weight_decay = _("weight_decay", 1e-5)           |
|              |        |         |     11:     print("weight decay is {}".format(weight_decay)) |
|              |        |         |     12:                                                      |
|              |        |         |     13:                                                      |
|              |        |         |     14: def main():                                          |
|              |        |         |     15:     parser = argparse.ArgumentParser()               |
+--------------+--------+---------+--------------------------------------------------------------+
$ ./main.py -h
usage: main.py [-h] [--weight-decay WEIGHT_DECAY] [--hp-save HP_SAVE]
               [--hp-load HP_LOAD] [--hp-list [{detail,yaml}]]
               [--hp-serial-format {auto,yaml,pickle}] [--hp-exit]

optional arguments:
  -h, --help            show this help message and exit
  --weight-decay WEIGHT_DECAY
  --hp-save HP_SAVE     Save hyperparameters to a file. The hyperparameters
                        are saved after processing of all other options
  --hp-load HP_LOAD     Load hyperparameters from a file. The hyperparameters
                        are loaded before any other options are processed
  --hp-list [{detail,yaml}]
                        List all available hyperparameters. If `--hp-list
                        detail` is specified, a verbose table will be print
  --hp-serial-format {auto,yaml,pickle}
                        Format of the saved config file. Defaults to auto. Can
                        be set to override auto file type deduction.
  --hp-exit             process all hpargparse actions and quit
```
(样例来自于 [hpargparse](TODO:link-to-hpargparse-example))

现在，我们既是**分布式**（可在任何地方写）又是**集中式**（可整体管理）。

我们的设计灵感来自软件国际化工具[gettext](https://www.gnu.org/software/gettext/)中常用的[下划线函数](https://www.gnu.org/software/gettext/manual/html_node/Mark-Keywords.html)。我们将超参数视为一条可翻译文本，而同一超参数不同的值对应于同一文本的不同“语言”。

我们通过静态解析源代码并提取定义和使用超参数时的上下文来实现上述目的。它遵循[代码即数据](https://en.wikipedia.org/wiki/Code_as_data)的思想。

另外，我们使用了`ast.literal_eval`使得在hpman中进行表达式求值非常安全。


# 安装

```bash
pip install hpman
```

# 使用方法



# 样例

`lib.py`:

```python
# File: lib.py
from hpman.m import _


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

from hpman.m import _

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

结果:

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

这是设计用于数据处理的核心库。您可能想要使用更好的前端：

- [CLI examples](TODO:link-to-hpargparse)
- [Jupyter examples](TODO:link-to-hpjupyter)
- [VSCode Extension](TODO:link-to-hpcode)

# 特性

## 设计原则

1. 低运行时开销。

2. 超参数的值可以是任何类型。

## 任意名称导入

超参数管理器是hpman最重要的对象。在整个教程中，我们都使用`from hpman.m import _`，并建议使用下划线（“_”，参考[gettext](https://www.gnu.org/software/gettext/)）作为导入名称，但实际上您可以使用所需的任何名称。

`hpman.m`模块配置为允许任意导入。无论您导入什么，都将始终是超参数管理器的对象，并且与“_”相同：

```bash
from hpman.m import _, hpm, hp, ddd, abc, hello
ddd('a', 1)
abc('a', 2)
_('hello', 3)
```

通过不同名称导入的超参数管理器是独立且并行工作的。具有相同名称的导入将被缓存；在相同过程中导入相同名称的对象将始终返回相同对象。

一些警告：

- 将这些导入的对象分配给变量将在静态解析中不起作用（将在以后解决），但在运行时有效（如果您跳过了解析阶段）。 例如。：

```python
# XXX: BAD EXAMPLE
from hpman.m import _
hello = _  # this breaks the rule
hello('a', 1)  # <-- hpman will not ware this 'a' hyperparameter.
```

- 变量与`hpman.m`导入具有相同的名称，将由hpman静态解析，但在运行时将无法按预期运行。 例如。：

```python
def func(*args, **kargs):
    pass

_ = func

_("a", 1)  # <-- hpman can do nothing with "_" at runtime

from hpman.m import _

print(_.parse_file(__file__).get_values())
# Will output "{'a': 1}", which is a "false positive" of hyperparameter
# occurrence.
```

## 定义超参数

hpman最基本（也是最常用）的功能是定义一个超参数。

```python
from hpman.m import _

def training_loop():
    # training settings
    batch_size = _('batch_size', 128)

    # first use of `num_layer` is recommend to come with default value
    print('num_layers = {}'.format(_('num__layers', 50)))

    # use it directly without storing the values
    if _('use_resnet', True):
	# second use of `num_layer` should not provide default value
	for i in range(_('num_layers')):
	    pass
```

一些警告：

1. 在相同超参数的所有事件中，**仅有一个**事件具有默认值，哪一个没有关系（您可以先使用，然后在后续事件中定义默认值）。

2. 超参数的名称必须是“文字字符串”。
   
3. 超参数的值可以是任意对象（变量，lambda函数，字符串等），但强烈建议仅使用**literal值**，该值由`ast.literal_eval`函数接受的值精确定义。它不仅使在下游框架（例如hpargparse）中的超参数的序列化变得更容易，而且还提高了不同编程语言和框架之间的超参数设置的互操作性。转储的超参数的也将更具可读性。

## 静态解析

我们采用静态解析来检索有关在源代码中使用超参数的位置和方式的信息，通过`_.parse_file` 和 `_.parse_source` 实现。

- `_.parse_file`接受文件路径、目录名或包含两者的列表。内部调用`_.parse_source`。
- `_.parse_source` 仅接受一段源代码字符串。

样例：

```python
_.parse_file(__file__)
_.parse_file('main.py')
_.parse_file('library_dir')
_.parse_file(['main.py', 'library_dir'])

_.parse_source('_("a", 1)')
```

解析是使用python标准库中提供的ast模块完成的。我们将所有函数调用与所需的语法进行匹配，以检测对超参数管理器的正确调用。

## Runtime Value Getter/Setter
## 运行时获取方法和设置方法

在运行时可以通过两种方式获取超参数的值：

1. 使用 `__call__` 语法: `_('varname')`

2. 使用专用函数: `_.get_value('varname')`

可以通过 `_.get_values()` 命令获取所有的超参数。

设置超参数只能用
```python
_.set_value('varname', value)
```

## 提示

**提示**旨在提供扩展hpman的机制。

它提供了一个接口，用于存储和检索在超参数定义时提供的任意信息。下游库和框架可以利用这些提供的信息更好地实现其自身目的。

例如，假设我们要创建一个用于在命令行界面设置超参数的argparse接口，用户可以编写如下内容

```python
_('optimizer', 'adam', choices=['adam', 'sgd'])
```

在他们的代码库和程序的入口点，我们可以检索这些信息并提供更好的argparse选项：

```python
# File: hints_example.py
from hpman.m import _
from hpman.hpm_db import L

import argparse

_('optimizer', 'adam', choices=['adam', 'sgd'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    _.parse_file(__file__)
    occurrences = _.db.select(lambda row: row.name == 'optimizer')
    oc = [
        oc
        for oc in occurrences
        if oc['hints'] is not None
    ][0]
    choices = oc['hints']['choices']
    value = oc['value']

    parser.add_argument('--optimizer', default=value, choices=choices)
    args = parser.parse_args()

    print('optimizer: {}'.format(args.optimizer))
```

用例如下：

```bash
$ python3 hints_example.py
optimizer: adam
$ python3 hints_example.py -h
usage: hints_example.py [-h] [--optimizer {adam,sgd}]

optional arguments:
  -h, --help            show this help message and exit
  --optimizer {adam,sgd}
$ python3 hints_example.py --optimizer sgd
optimizer: sgd
$ python3 hints_example.py --optimizer rmsprop
usage: hints_example.py [-h] [--optimizer {adam,sgd}]
hints_example.py: error: argument --optimizer: invalid choice: 'rmsprop' (choose from 'adam', 'sgd')
```

该样例可以在 [examples/02-hints](examples/02-hints) 找到。

## Nested Hyperparameters

当超参数数量增多时，我们经常将超参数分为若干族，使用相同的前缀方便管理。

你可以批量操作同一族的超参数。如将超参数导出成如下结构的yaml，提高了可读性。也可以直接导入树状结构的yaml。

```yaml
discriminator:
  in_channels: 3
  spectral: true
  norm: 'instance'
  activation: 'leaky_relu'
  residual: true
  input_size: [512, 512]
```

**警告:** 一个超参数不能同时指向一个值和一棵树，你可以通过`set_value`和`set_tree`分别指明超参数的类型是值还是树。当你通过下划线函数定义默认值时，会被视为是值。
所以如下代码

```python
_('a', {'b': 1})    # 被视为name='a'的超参数，默认值为{'b': 1}。此时a是值。
_('a.b')            # 被视为超参树a中的b，此时a是树。
```

在运行时会抛出异常：

```bash
KeyError: '`a.b` not found'
```

在静态解析时会抛出异常：

```bash
hpman.primitives.ImpossibleTree: node `a` has is both a leaf and a tree.
```

**缺点和兼容性破坏：你不能使用两个超参数，一个是另一个的前缀 (被‘.’分隔)。**
因为树的名字允许为空，所以你仍然可以在超参数的名字中使用`.`，包括以`.`开头，以`.`结尾，或连续的`.`都是合法的。例如 `_(".hpman is a good...man.")`.

# Contributing


# License

[MIT](LICENSE) © MEGVII Research