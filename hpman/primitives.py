from typing import Union, Sequence, Any, AnyStr


# -- Exceptions
class DoubleAssignmentException(Exception):
    pass


class NotLiteralNameException(Exception):
    pass


class NotLiteralEvaluable(Exception):
    pass


# -- Sentinels
class EmptyValue:
    pass


# -- Types
Scalar = Union[None, int, float, bool, AnyStr, Any, EmptyValue]
Vector = Sequence[Scalar]
Primitive = Union[Scalar, Vector]
