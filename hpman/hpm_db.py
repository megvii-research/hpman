import ast
import enum
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from .primitives import DoubleAssignmentException, EmptyValue, ImpossibleTree, Primitive
from .source_helper import SourceHelper


class HyperParameterPriority(enum.IntEnum):
    PRIORITY_PARSED_FROM_SOURCE_CODE = 1  # multiple occurrence
    PRIORITY_SET_FROM_CALLABLE = 2  # single occurrence
    PRIORITY_SET_FROM_SETTER = 3  # single occurrence


P = HyperParameterPriority


class HyperParameterOccurrence:
    """A single occurrence of a statically pasred hyperparameter."""

    name = None  # type: str
    """Name of the hyperparameter"""

    value = EmptyValue()
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

    source_helper = None  # type: SourceHelper
    """Source infomation and helper functions for this occurrence.
    """

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(HyperParameterOccurrence, k):
                setattr(self, k, v)

    @property
    def has_default_value(self):
        return not isinstance(self.value, EmptyValue)

    @property
    def value_priority(self):
        return self.priority * 10 - isinstance(self.value, EmptyValue)


class HyperParamNode:
    def __init__(self, name: str = ""):
        self.name = name
        self._db = []  # type: List[HyperParameterOccurrence]

    def push(self, occ: HyperParameterOccurrence):
        """Push occurrence to current node, sort by priority."""
        if not len(self):
            self._db.append(occ)
            return

        top = self.get()
        assert occ.name == top.name  # type: ignore

        # push from static parsing
        if occ.priority == P.PRIORITY_PARSED_FROM_SOURCE_CODE:
            self._db.append(occ)
            self._db.sort(key=lambda x: -x.value_priority)
            return

        pos, replacement = -1, False
        for i, v in enumerate(self._db):
            pos = i
            # if current priority is lower than new, insert here
            if v.value_priority < occ.value_priority:
                break
            # only one slot for each priority
            elif v.value_priority == occ.value_priority:
                replacement = True
                break
        else:
            pos = len(self._db)

        if replacement:
            self._db[pos] = occ
        else:
            self._db.insert(pos, occ)

    def get(self) -> Optional[HyperParameterOccurrence]:
        """Get the occurrence with highest priority."""
        if len(self) == 0:
            return None

        return self._db[0]

    @property
    def db(self) -> List[HyperParameterOccurrence]:
        """Get all occurrences."""
        if len(self) == 0:
            return []

        return self._db

    @property
    def value(self) -> Any:
        """Get the value of the top occurrence."""
        if len(self) == 0:
            return EmptyValue()

        return self._db[0].value

    @property
    def empty(self):
        """Node with no occurrence or empty occurrence is empty."""
        return isinstance(self.value, EmptyValue)

    @classmethod
    def format_occurrence(cls, occurrence: HyperParameterOccurrence, **kwargs) -> str:
        """Format a single occurrence.

        :param occurrence: the occurrence to be formated
        """
        assert occurrence is not None
        return occurrence.source_helper.format_given_filename_and_lineno(
            occurrence.filename, occurrence.lineno
        )

    def _check_source_code_double_assigment(self, occ):
        for item in self._db:
            if not item.priority == P.PRIORITY_PARSED_FROM_SOURCE_CODE:
                continue

            if item.has_default_value:
                error_msg = (
                    "Duplicated default values:\n"
                    "First occurrence:\n"
                    "{}\n"
                    "Second occurrence:\n"
                    "{}\n"
                ).format(self.format_occurrence(item), self.format_occurrence(occ))
                raise DoubleAssignmentException(error_msg)

    def __len__(self):
        return len(self._db)


class HyperParamTree:

    """A tree-mapping of HyperParameterOccurrence.
    It is required that only one of the underlying occurrences should have a default value.
    """

    DICT_ANNOTATION = "__is_dict__"
    """Annotation string to indicate that a dict is not a tree.
    """

    def __init__(self, separator: str = ".", name: str = ""):
        """
        :param separator: character to separate nested keys.
        :param name: name of the current tree level.
        """
        assert len(separator) == 1

        self.sep = separator
        self.name = name
        self.children = {}  # type: Dict[str, HyperParamTree]
        self.node = None  # type: Optional[HyperParamNode]

    def flatten(self) -> Iterator[HyperParamNode]:
        """Flatten the tree of hyperparamters to a sequence of HyperParameterOccurrences"""

        def _wrapper(cur: HyperParamTree):
            if cur.is_leaf() and (cur.node is not None) and (not cur.node.empty):
                yield cur.node

            for v in cur.children.values():
                yield from _wrapper(v)

        yield from _wrapper(self)

    def count(self):
        """Get the number of all non-empty hyperparamters."""
        acc = 0
        for node in self.flatten():
            acc += 1
        return acc

    @property
    def empty(self):
        """A tree with neither children nor node is empty."""
        return (not self.children) and self.node is None

    def is_leaf(self):
        """If tree has no children, it is a leaf node."""
        return not self.children

    def is_branch(self):
        """A valid tree with children is a branch or tree node."""
        if not self.is_valid(strict=False):
            return False

        return len(self.children) > 0

    def is_valid(self, strict=False):
        """Whether the current top node is valid.

        :param strict: In strict mode, nodes with both node value and children
            are strictly invalid, often used in static parsing.
            In non-strict mode, if node value is set in static parser,
            node is still valid, often used in runtime.

        :note:
            Non-strict mode is useful when user needs to set nested params in
            runtime (e.g. loading from yaml).
            For example, a user can define a hyperparamter
            with ``_('group', {'foo': bar})`` and then manually set it with
            ``_.set_tree({'group': {'foo': baz} })``. In this case, ``group`` was
            a leaf node by static parser, but converted to a tree node in runtime.
        """
        # leaf with value is always valid
        if self.is_leaf():
            return True

        # non-leaf without current node is valid
        if not self.node or self.node.empty:
            return True

        # if node is set in static parser, valid
        if not strict:
            occ = self.node.get()
            if occ.priority < P.PRIORITY_SET_FROM_SETTER:
                return True

        # both children and node are set, impossible tree
        return False

    def tree_values(self, annotate_dict: bool = False) -> Dict[str, Any]:
        """Get all hyperparamter in tree structure as a dict.

        :param annotate_dict: If a leaf node has value type of dict,
            add a dict annotation so it can be safely convert back to the same
            tree structure. This is often used for safe serialization
            (e.g. dump as yaml).
        """

        assert self.is_branch()

        def _walk(tree: HyperParamTree, level: Dict[str, Any]):
            for k, v in tree.children.items():
                assert v.is_valid(strict=False)
                if v.is_leaf():
                    assert v.node is not None
                    val = v.node.value
                    if isinstance(val, dict) and annotate_dict:
                        val = val.copy()  # make a shallow copy
                        val[self.DICT_ANNOTATION] = True
                    level[k] = val
                else:
                    level[k] = {}
                    _walk(v, level[k])

        ret = {}  # type: Dict[str, Any]
        _walk(self, ret)
        return ret

    def validate(self):
        """Recursively validate current tree."""
        if not self.is_valid(strict=True):
            raise ImpossibleTree(
                "`{}` is both a leaf and a tree.".format(self.node.name)
            )

        if self.is_branch():
            for v in self.children.values():
                v.validate()

        return True

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
        tree = self._allocate(occurrence.name)  # type: HyperParamTree
        set_from_src = occurrence.priority == P.PRIORITY_PARSED_FROM_SOURCE_CODE
        if tree.node is None:
            tree.node = HyperParamNode(occurrence.name)

        if set_from_src:  # multiple occurrence is permitted
            if occurrence.has_default_value:
                if source_helper is not None:
                    occurrence.source_helper = source_helper
                tree.node._check_source_code_double_assigment(occurrence)

        tree.node.push(occurrence)
        if not tree.is_valid(strict=True):
            raise ImpossibleTree(
                "node `{}` has is both a leaf and a tree.".format(occurrence.name)
            )

    def _allocate(self, key: str) -> "HyperParamTree":
        def _wrapper(tree: HyperParamTree, route: Sequence[str]):
            if not route:
                return tree

            k, *rest = route
            if k not in tree.children:
                tree.children[k] = HyperParamTree(separator=tree.sep, name=k)

            return _wrapper(tree.children[k], rest)

        return _wrapper(self, key.split(self.sep))

    def get(self, key: str) -> Optional["HyperParamTree"]:
        if not key:
            return self

        cur, *rest = key.split(self.sep, maxsplit=1)
        if cur not in self.children:
            return None

        rest_key = rest[0] if rest else ""

        return self.children[cur].get(rest_key)

    def __setitem__(self, key: str, value: Primitive):
        self.push_occurrence(
            HyperParameterOccurrence(
                name=key, value=value, priority=P.PRIORITY_SET_FROM_SETTER
            )
        )
