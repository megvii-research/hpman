import collections
import enum
import functools
import ast
from typing import Callable, Dict, List, Optional, Union, DefaultDict, Any

from attrdict import AttrDict  # type: ignore

from .primitives import DoubleAssignmentException, EmptyValue
from .source_helper import SourceHelper


class HyperParameterPriority(enum.IntEnum):
    PRIORITY_PARSED_FROM_SOURCE_CODE = 1  # multiple occurrence
    PRIORITY_SET_FROM_CALLABLE = 2  # single occurrence
    PRIORITY_SET_FROM_SETTER = 3  # single occurrence


P = HyperParameterPriority


class HyperParameterOccurrence(AttrDict):
    """A single occurrence of a statically pasred hyperparameter. Subclasses
    dict.
    """

    name = None  # type: str
    """Name of the hyperparameter"""

    value = EmptyValue()  # type: Any
    """Value of the hyperparameter. An instance of :class:`.primitives.EmptyValue`
    should present if value is not set."""

    priority = None  # type: HyperParameterPriority
    """Priority of this hyperparameter occurrence. The value of the highest
    priority of all the occurrences of the same hyperparameter will be denoted
    as "the value of this hyperparameter". See :class:`HyperParameterPriority`
    for details about the meaning of each priority.
    """

    filename = None  # type: str
    """Filename in which this hyperparameter occurs. Will only present in
    parsed hyperparameters"""

    lineno = None  # type: int
    """In which line of the file this hyperparameter occurs. Will only present
    in parsed hyperparameters """

    ast_node = None  # type: ast.AST
    """The parsed `ast.AST` object of this occurrence. Will only present
    in parsed hyperparameters"""

    hints = None  # type: Dict[str, Any]
    """Hints provided by user of this occurrence of the hyperparameter.  Will
    only present in parsed hyperparameters """

    # XXX: In python 3.6, we would use `attr_dict_bind` library to implement
    #     attribute dict binding mechanism with user defined attributes
    #     straighforwardly.
    #     However, to accommodate python 3.5, we implement the same function
    #     using `attrdict` along with the following ugly hacks.
    __defaults = {
        "name": None,
        # This empty value instance is vital; we rely on this exact sentinel
        # object group all empty values.
        "value": EmptyValue(),
        "priority": None,
        "filename": None,
        "lineno": None,
        "ast_node": None,
        "hints": None,
    }

    def __init__(self, *args, **kwargs):
        # Make a **shallow** copy of default values (as we need the EmptyValue
        # sentinel to be the same across instances of HyperParameterOccurrence)
        d = self.__defaults.copy()

        # get user passed dict initialization
        v = dict(*args, **kwargs)

        # ... and overrides defaults
        d.update(v)

        for name in self.__defaults:
            if hasattr(self, name):
                # XXX: remove user defined attributes as AttrDict does not works
                # with them
                delattr(type(self), name)
        super().__init__(*args, **d)

    @property
    def has_default_value(self):
        return not isinstance(self.value, EmptyValue)


class HyperParameterDB(list):
    """A list of HyperParameterOccurrence. It is required that only one of the
    underlying occurrences should have a default value. Subclasses list. It
    provides SQL/pandas-like syntax to access the data.

    :note: This *DB* is quite functional and does not provide the concept of
        *view*. Most operations provided return a new instance. We provide
        back-reference ability by assign an auto increment index to every
        entry.
    """

    index_count = None  # type: int
    """Auto increment counter"""

    def __init__(self, *args, **kwargs):
        self.index_count = 0
        super().__init__(*args, **kwargs)

    # -- database operations
    def copy(self):
        return HyperParameterDB(super().copy())

    def group_by(self, column: str) -> Dict[str, "HyperParameterDB"]:
        """Group data by given attribute/column.

        :param column: The attribute to be grouped by.
        """
        groups = collections.defaultdict(
            HyperParameterDB
        )  # type: DefaultDict[str, HyperParameterDB]
        for i in self:
            groups[getattr(i, column)].append(i)
        return groups

    def indexing(self, idx: Union[int, List[int]]):
        """Indexing using a integer or a list of integers.

        :param idx: index of HyperParameterOccurrence to be fetched
        """
        if isinstance(idx, int):
            return self[idx]
        if isinstance(idx, list):
            return HyperParameterDB([self[i] for i in idx])
        raise IndexError("Unknown index: {}".format(idx))

    def select(
        self, where: Callable[[HyperParameterOccurrence], bool]
    ) -> "HyperParameterDB":
        """Select rows from database.

        :param where: a function takes a row and returns whether this row
            should be retained.
        """
        return HyperParameterDB([i for i in self if where(i)])

    def count(self, where: Callable[[HyperParameterOccurrence], bool]) -> int:
        """Count number of rows match given condition. Equivalent to
        len(self.select(where))
        """
        return sum(1 for i in self if where(i))

    def extract_column(self, column: str) -> List[object]:
        """Extract one column of values.

        :param column: column name to be extracted

        :return: list of values.
        """
        return [i[column] for i in self]

    def choose_columns(self, *columns: List[str]) -> "HyperParameterDB":
        """Extract columns to form a new database.

        :param columns: list of column names to be extracted.
        """
        return HyperParameterDB([{c: i[c] for c in columns} for i in self])

    def apply(
        self, func: Callable[[HyperParameterOccurrence], HyperParameterOccurrence]
    ) -> "HyperParameterDB":
        """Apply func on each row, which modifies old db.

        :param func: a function that takes a row, modifies it inplace.
        :return: self
        """
        for i in self:
            func(i)
        return self

    def reduce(
        self,
        reduce_func: Callable[[object, HyperParameterOccurrence], object],
        initial=EmptyValue(),
    ) -> object:
        """Reduce the sequence to a single value. Raises ValueError if there's
        no items to be reduced.

        :param reduce_func: function takes two arguments, the first one is
            the previous result, and second is a new coming value in the sequence.
        :param initial: if given, will be sent to reduce_func as its first argument
            in the beginning; otherwise, the first element in the sequence is sent.
        """
        # TODO: more memory efficient implementation

        if not isinstance(initial, EmptyValue):
            value = initial
            i = 0
        else:
            if len(self) == 0:
                raise ValueError("No object to be aggregated.")
            value = self[0]
            i = 1

        for j in range(i, len(self)):
            value = reduce_func(value, self[j])

        return value

    def empty(self) -> bool:
        """Whether the db is empty"""
        return len(self) == 0

    def sorted(
        self, key: Callable[[HyperParameterOccurrence], int], reverse: bool = False
    ) -> "HyperParameterDB":
        """Sort the rows of the db. See builtin function `sorted`"""
        return HyperParameterDB(sorted(self, key=key, reverse=reverse))

    def any(self, func: Callable[[HyperParameterOccurrence], bool]) -> bool:
        """If **one** of the results after applying the given function to each row
        is True, then returns true. The evaluation is short-circuited.

        :param func: The funcion maps a row to a boolean value, which will be
            applied to each row of the database.
        """
        return any(map(func, self))

    def all(self, func: Callable[[HyperParameterOccurrence], bool]) -> bool:
        """If **all** of the results after applying the given function to each row
        is True, then returns true. The evaluation is short-circuited.

        :param func: The funcion maps a row to a boolean value, which will be
            applied to each row of the database.
        """
        return all(map(func, self))

    def find_first(
        self, where: Callable[[HyperParameterOccurrence], bool]
    ) -> Optional[HyperParameterOccurrence]:
        """Find the first row which matches given condition.

        :param where: The function takes a row and returns a boolean value,
            indicating whether a row should be retained.
        :return: A row is returned if at least one match is found; otherwise
            None will be returned.
        """
        for i in self:
            if where(i):
                return i
        return None

    @classmethod
    def format_occurrence(cls, occurrence: HyperParameterOccurrence, **kwargs) -> str:
        """Format a single occurrence.

        :param occurrence: the occurrence to be formated
        """
        assert occurrence is not None
        return occurrence["source_helper"].format_given_filename_and_lineno(
            occurrence["filename"], occurrence["lineno"]
        )

    def _do_push_occurrence(self, occurrence):
        occurrence["index"] = self.index_count
        self.index_count += 1
        self.append(occurrence)

    def _do_set_occurrence(self, idx, occurrence):
        s = self[idx]
        occurrence["index"] = s["index"]
        self[idx] = occurrence

    def _check_source_code_double_assigment(self, occurrence):
        s = self.select(
            lambda row: (
                row.name == occurrence.name
                and row.priority == P.PRIORITY_PARSED_FROM_SOURCE_CODE
            )
        )

        if s.any(L.has_default_value):
            error_msg = (
                "Duplicated default values:\n"
                "First occurrence:\n"
                "{}\n"
                "Second occurrence:\n"
                "{}\n"
            ).format(
                s.format_occurrence(s.find_first(L.has_default_value)),
                s.format_occurrence(occurrence),
            )
            raise DoubleAssignmentException(error_msg)

    def push_occurrence(
        self,
        occurrence: HyperParameterOccurrence,
        *,
        source_helper: Optional[SourceHelper] = None
    ) -> None:
        """Add an hyperparameter occurrence. This method can only be used
        in static parsing phase.
        """
        assert isinstance(occurrence, HyperParameterOccurrence), (
            type(occurrence),
            occurrence,
        )
        set_from_src = occurrence.priority == P.PRIORITY_PARSED_FROM_SOURCE_CODE

        if set_from_src:  # multiple occurrence is permitted
            if occurrence.has_default_value:
                if source_helper is not None:
                    occurrence["source_helper"] = source_helper
                self._check_source_code_double_assigment(occurrence)
            self._do_push_occurrence(occurrence)
        else:  # only one occurrence is permitted
            s = self.select(
                lambda row: (
                    row.name == occurrence.name and row.priority == occurrence.priority
                )
            )
            if s.empty():
                self._do_push_occurrence(occurrence)
            else:
                assert len(s) == 1, len(s)
                self._do_set_occurrence(s[0]["index"], occurrence)


class HyperParameterDBLambdas:
    # -- sort lambdas
    # sort first by priority, then by value non-emptiness
    @staticmethod
    def value_priority(row: HyperParameterOccurrence):
        return -(row.priority * 10 - isinstance(row.value, EmptyValue))

    @staticmethod
    def order_by(column: str):
        return lambda row: getattr(row, column)

    # -- select lambdas
    @staticmethod
    def has_default_value(row):
        return not isinstance(row.value, EmptyValue)

    @staticmethod
    def exist_attr(attr):
        return lambda row: hasattr(row, attr) and (getattr(row, attr) is not None)

    @staticmethod
    def of_name(name):
        return lambda row: row.name == name

    @staticmethod
    def of_name_prefix(prefix):
        return lambda row: row.name.startswith(prefix)

    @staticmethod
    def of_name_suffix(suffix):
        return lambda row: row.name.endswith(suffix)

    @staticmethod
    def of_value(value):
        return lambda row: row.value == value

    @staticmethod
    def of_priority(priority):
        return lambda row: row.priority == priority

    @staticmethod
    def apply_column(column, func):
        @functools.wraps(func)
        def wrapper(row):
            old_value = getattr(row, column)
            new_value = func(old_value)
            setattr(row, column, new_value)

        return wrapper

    @staticmethod
    def land(*args):
        """Logical and"""
        return lambda row: all(f(row) for f in args)

    @staticmethod
    def lor(*args):
        """Logical or"""
        return lambda row: any(f(row) for f in args)

    @staticmethod
    def lnot(func):
        """Logical not"""
        return lambda row: not func(row)


L = HyperParameterDBLambdas
