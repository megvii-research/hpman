from typing import Mapping, Sequence, TypeVar, Union


# -- Exceptions
class DoubleAssignmentException(Exception):
    pass


class NotLiteralNameException(Exception):
    pass


class NotLiteralEvaluable(Exception):
    pass


class ImpossibleTree(ValueError):
    pass


# -- Sentinels
class EmptyValue:
    pass


# -- Types
T = TypeVar("T")
Primitive = Union[None, T, Sequence[T], EmptyValue]
FlatMapping = Mapping[str, Primitive]
TreeMapping = Mapping[str, Union[Primitive, TypeVar("TreeMapping")]]  # type: ignore
