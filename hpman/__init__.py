import sys

from .__version__ import __author__, __author_email__, __title__, __url__, __version__
from .hpm import (
    DoubleAssignmentException,
    EmptyValue,
    HyperParameterManager,
    NotLiteralEvaluable,
    NotLiteralNameException,
    SourceHelper,
)
from .hpm_db import (
    HyperParameterDB,
    HyperParameterDBLambdas,
    HyperParameterOccurrence,
    HyperParameterPriority,
    L,
    P,
)

# moneky patch to enable ``from hpman.m import whatever```
from .hpm_zoo_monkey_patch import HPMZooModule

m = HPMZooModule(__name__ + ".m", HPMZooModule.__doc__)
sys.modules[m.__name__] = m

del sys
del HPMZooModule

__all__ = [
    "__author__",
    "__author_email__",
    "__title__",
    "__url__",
    "__version__",
    "DoubleAssignmentException",
    "EmptyValue",
    "HyperParameterManager",
    "NotLiteralEvaluable",
    "NotLiteralNameException",
    "SourceHelper",
    "HyperParameterDB",
    "HyperParameterDBLambdas",
    "HyperParameterOccurrence",
    "HyperParameterPriority",
    "L",
    "P",
]
