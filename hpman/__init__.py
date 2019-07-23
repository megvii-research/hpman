from .hpm import (
    DoubleAssignmentException,
    NotLiteralNameException,
    EmptyValue,
    NotLiteralEvaluable,
    SourceHelper,
    HyperParameterManager,
)

from .hpm_db import (
    HyperParameterOccurrence,
    HyperParameterDB,
    HyperParameterPriority,
    P,
    HyperParameterDBLambdas,
    L,
)

# moneky patch to enable ``from hpman.m import whatever```
from .hpm_zoo_monkey_patch import HPMZooModule
import sys

m = HPMZooModule(__name__ + ".m", HPMZooModule.__doc__)
sys.modules[m.__name__] = m

del sys
del HPMZooModule
