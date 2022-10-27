import ast
import glob
import os
from typing import Any, Dict, Optional, Set

from .hpm_db import (
    HyperParameterOccurrence,
    HyperParameterPriority,
    HyperParamNode,
    HyperParamTree,
    P,
)
from .primitives import (
    DoubleAssignmentException,
    EmptyValue,
    FlatMapping,
    ImpossibleTree,
    NotLiteralEvaluable,
    NotLiteralNameException,
    Primitive,
    TreeMapping,
)
from .source_helper import SourceHelper

# -- Data Structures
# Data structure hierarchy:
#     HyperParameterOccurrence
#                 |
#                 v
#     HyperParameterTree
#                 |
#                 v
#     HyperParameterManager


class HyperParameterManager:
    """HyperParameterManager manages a data structure of hyperparamters
    throughout their lifecycle. A lifecycle of hyperparameter are divided into
    two phases: parsing-time and runtime. In parsing-time, source code are
    parsed to (A) set of user-defined hyperparameters with default values;
    while in runtime, user can (B) set/get defaults calling
    HyperParameterManager object, and (C) set values intentionally using
    methods. A HyperParameterManager object is usually created as some
    light-weight names, such as underscore "_". This is called a placeholder,
    and is vital to the parsing of source code. Hyperparameter values set
    by (A), (B), (C) three methods are of increasing priority; the latter may
    overwrite the value of the former one. We call it "Hyperparameter Value
    Trilogy"
    """

    placeholder = None  # type: str
    """Placeholder name of the HyperParameterManager object.
    """

    separator = None  # type: str
    """Separator character for nested hyperparameter names.
    """

    tree = None  # type: HyperParamTree
    """Tree style hyperparameter database. ANYTHING you want is here.
    """

    def __init__(self, placeholder: str, separator: str = "."):
        """Create a hyperparameter manager.

        :param placeholder: placeholder name of this HyperParameterManager
            object. It is important to store this object in a variable in the name
            of this placeholder prior to defining hyperparameters by calling the
            object.

        :param separator: separator character for nested hyperparameter names.
        """
        self.placeholder = placeholder
        assert len(separator) == 1
        self.separator = separator

        # The "Hyperparameter Value Triology"
        self.tree = HyperParamTree()

    def parse_file(self, path: str) -> "HyperParameterManager":
        """Parse given file to extract hyperparameter settings.

        :param path: The path to a python source code, directory, or a list of both
        :return: the object itself
        """
        paths = None
        if not isinstance(path, list):
            paths = [path]
        else:
            paths = path

        parsing_files = set()  # type: Set[str]
        for _path in paths:
            if os.path.isdir(_path):
                for filename in sorted(
                    glob.glob(os.path.join(_path, "**/*.py"), recursive=True)
                ):  # sort for debugging stability
                    if filename not in parsing_files:
                        parsing_files.add(filename)
            elif os.path.exists(_path):
                # _path is a file
                if _path not in parsing_files:
                    parsing_files.add(_path)
            else:
                raise FileNotFoundError(_path)

        for _file in sorted(parsing_files):  # sort for debugging stability
            with open(_file) as f:
                self.parse_source(f.read(), _file)

        return self

    # parsing-time methods
    # TODO: flatten the underlying data structure (to something like a SQL table).
    def parse_source(
        self, source: str, filename: str = "<unknown>"
    ) -> "HyperParameterManager":
        """Parse given string source to extract hyperparameter settings.

        :param source: a string of python code with correct line breakings
        :param filename: filename of the python code if have, which is used to
            set attribute of HyperParameter occurrence

        :note: The parsed results can be seen as a dict of the following structure:

            .. code:: python

                  {
                    "hp0": [
                        {
                            "name": "hp0",
                            "filename": "xxx/xxx.py",
                            "value": <EmptyValue>,
                            "lineno": 123,
                            "ast_node": <_ast.Call at 0x7fdead3da456>,
                            "hints": {},
                            ...,  # There will be potentially more attributes in the future
                        },
                        {
                            "name": "hp0",
                            "filename": "yyy/yyy.py",
                            "value": "hello world!",
                            "lineno": 345,
                            "ast_node": <_ast.Call at 0x7fdead3dabee>,
                            "hints": {'a': 1, 'b': 2},
                        },
                        ...,
                    ],
                     "hp1": [
                         {
                            "name": "hp1",
                            "filename": "xxx/yyy.py",
                            "value": [12345, 2, 3],
                            "lineno": 11,
                            "ast_node": <_ast.Call at 0x7fdeadbeef56>,
                            "hints": {},
                        },
                        ...
                    ],
                    "lr_sched": [
                         {
                            "name": "lr_sched",
                            "filename": "yyy/zzz.py",
                            "value": {
                                "type": "linear-decay-cyclic",
                                "learning_rate": 10,
                                "period": 5000,
                                "restart_steps": [50000, 70000, 80000],
                                "post_proc_func": <_ast.Name at 0x7f31203fe588>,
                            },
                            "lineno": 998,
                            "ast_node": <_ast.Call at 0x7fbeefdead56>,
                            "hints": {"type": dict},
                        },
                    ],
                  }

            Rules for the value of "value" depends on the type of parsed ast
            node.  The correspondance between node types and its actions are
            depicted as follows:

            1. if ``ast.literal_eval`` returns without exception, the the evaluated results are filled in the dict.
            2. otherwise a :class:`.primitives.NotLiteralEvaluable` sentinel object is filled
        """
        source_helper = SourceHelper(source)

        root_node = ast.parse(source, filename)
        for node in ast.walk(root_node):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)  # noqa
                and (node.func.id == self.placeholder)  # noqa
            ):
                # Check the number of positional arguments
                if len(node.args) < 1 or len(node.args) > 2:
                    raise Exception(
                        "number of positional args should be in range [1, 2], (was {} args), {}:L{}".format(
                            len(node.args), filename, node.lineno
                        )
                    )

                # Check hyperparameter name
                if not isinstance(node.args[0], ast.Str):
                    raise NotLiteralNameException(
                        "hp-name should be literal-string: L{}".format(node.lineno)
                    )

                # Literal evaluate the hyperparameter name
                name = ast.literal_eval(node.args[0])
                lineno = node.lineno

                # Parse the name and the default value
                ast_node = None
                if len(node.args) == 2:
                    ast_node = node.args[1]

                    try:
                        value = ast.literal_eval(node.args[1])
                    except ValueError:
                        value = NotLiteralEvaluable()
                else:
                    value = EmptyValue()

                # Parse hints
                # IMPORTANT: we demand hints to be literal evaluable (for now)
                hints = {}
                if hasattr(node, "keywords"):
                    for k in node.keywords:
                        try:
                            v = ast.literal_eval(k.value)
                        except ValueError:
                            raise NotLiteralEvaluable(
                                "Value of hint keyword `{}` is not literal evaluable: \n{}".format(
                                    k.arg,
                                    SourceHelper.format_given_filename_and_source_and_lineno(
                                        filename, source, lineno
                                    ),
                                )
                            )
                        hints[k.arg] = v

                # Construct an occurrence
                occ = HyperParameterOccurrence(
                    name=name,
                    value=value,
                    filename=filename,
                    lineno=lineno,
                    ast_node=ast_node,
                    hints=hints,
                    priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE,
                )
                self.tree.push_occurrence(occ, source_helper=source_helper)

        self.tree.validate()
        return self

    # runtime methods
    def exists(self, hp_name: str) -> bool:
        """Whether a hyperparameter exists

        :param hp_name: The name of the hyperparameter
        """
        value = self.get_value(hp_name, raise_exception=False)
        if isinstance(value, EmptyValue):
            return False
        return True

    def get_value(self, name: str, raise_exception: bool = True) -> TreeMapping:
        """Get the authoritative value of a hyperparameter.
        Will raise an exception if value does not exist by default.

        :param hp_name: The name of the hyperparameter
        :param raise_exception: Defaults to True; set false to suppress
            exception. In this case, the missing value will be an instance
            of :class:`.primitives.EmptyValue`

        :return: Return the stored value if found. Otherwise, if raise_exception is False,
            an :class:`.primitives.EmptyValue` object is returned.
        """

        tree = self.tree.get(name)

        if tree is None or tree.empty:
            val = EmptyValue()  # type: ignore
        elif tree.is_leaf():
            assert tree.node is not None
            val = tree.node.value  # type: ignore
        elif tree.is_branch():
            val = tree.tree_values()  # type: ignore

        if isinstance(val, EmptyValue):
            if raise_exception:
                raise KeyError("`{}` not found".format(name))

        return val  # type: ignore

    def get_occurrence(self, name: str) -> Optional[HyperParameterOccurrence]:
        """
        :param hp_name: The name of the hyperparameter

        :return: a :class:`.hpm_db.HyperParameterOccurrence` object or None
        """

        tree = self.tree.get(name)
        if tree is None or tree.empty:
            return None

        if tree.is_leaf():
            assert tree.node is not None
            return tree.node.get()

        return None

    def get_values(self) -> FlatMapping:
        """Get all current available hyperparameters and their values.

        :return: dict of name to value.
        """

        return {
            node.get().name: node.value for node in self.tree.flatten()  # type: ignore
        }

    def get_tree(self, prefix: str = "", annotate_dict: bool = False) -> TreeMapping:
        """Get subtree of prefix from hyperparamter tree.

        :param annotate_dict: If a leaf node has value type of dict,
          add a dict annotation so it can be safely convert back to the same
          tree structure. This is often used for safe serialization
          (e.g. dump as yaml).
        """
        if self.tree.empty:
            return {}

        tree = (
            self.tree.get(prefix) if prefix else self.tree
        )  # type: Optional[HyperParamTree]

        if tree is None:
            return {}

        assert tree.is_branch

        return tree.tree_values(annotate_dict=annotate_dict)

    def set_value(self, name: str, value: Primitive) -> "HyperParameterManager":
        """Runtime setter. Set value with the highest priority."""
        self.tree[name] = value
        return self

    def set_values(self, values: FlatMapping) -> "HyperParameterManager":
        """Runtime setter. Set a dict of values with the highest priority."""
        for k, v in values.items():
            self.tree[k] = v
        return self

    def set_tree(
        self, tree_values: TreeMapping, prefix: str = ""
    ) -> "HyperParameterManager":
        """Runtime setter.
        Set a tree dict of nested values with the highest priority.

        :param tree_values: nested hyperparameter names and values recursively
            structured as Mapping[str, [Mapping, Primitive]]. As an exception, if
            :attr:`.hpm_db.HyperParamTree.DICT_ANNOTATION` is set, it would be treated
            as a node of dict instead of a tree.

        :param prefix: the subtree prefix of hyperparameter tree to set.
            If prefix is empty, the top tree will be set.
        """
        if not isinstance(prefix, str):
            raise TypeError("Tree prefix must be a string.")

        def make_flat_tree(tv: Dict[str, Any], acc: Dict[str, Any], key: str):
            if not isinstance(tv, dict):
                acc[key] = tv
                return
            elif HyperParamTree.DICT_ANNOTATION in tv:
                is_dict = tv.pop(HyperParamTree.DICT_ANNOTATION)
                if is_dict:
                    acc[key] = tv
                    return

            key_prefix = [key] if key else []
            for k, v in tv.items():
                if not isinstance(k, str):
                    raise ImpossibleTree(
                        "Tree keys must be strings, but '{}.{}' is a '{}'.".format(
                            key_prefix, k, type(k)
                        )
                    )
                make_flat_tree(v, acc, self.separator.join(key_prefix + [k]))

        flat_tree = {}  # type: Dict[str, Any]
        make_flat_tree(tree_values, flat_tree, prefix)  # type: ignore

        return self.set_values(flat_tree)

    def __call__(self, hp_name: str, hp_value: EmptyValue = EmptyValue(), **hints):
        """Runtime callable setter and getter. Will set the value with
        intermediate priority.
        """
        # TODO: record runtime meta-info (filename, lineno, etc.) as well
        # XXX: recording TOO MUCH in runtime may harm performance
        if not isinstance(hp_value, EmptyValue):
            self.tree.push_occurrence(
                HyperParameterOccurrence(
                    name=hp_name, value=hp_value, priority=P.PRIORITY_SET_FROM_CALLABLE
                )
            )
        return self.get_value(hp_name)
