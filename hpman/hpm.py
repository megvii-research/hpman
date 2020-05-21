import ast
import glob
import os
from typing import Optional, Set

from .hpm_db import (
    HyperParameterDB,
    HyperParameterDBLambdas,
    HyperParameterOccurrence,
    HyperParameterPriority,
    L,
    P,
)
from .primitives import (
    DoubleAssignmentException,
    EmptyValue,
    NotLiteralEvaluable,
    NotLiteralNameException,
)
from .source_helper import SourceHelper

# -- Data Structures
# Data structure hierarchy:
#     HyperParameterOccurrence
#                 |
#                 v
#     HyperParameterDB
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

    db = None  # type: HyperParameterDB
    """Hyperparameter database. ANYTHING you want is here.
    """

    def __init__(self, placeholder: str) -> None:
        """Create a hyperparameter manager.

        :param placeholder: placeholder name of this HyperParameterManager
            object. It is important to store this object in a variable in the name
            of this placeholder prior to defining hyperparameters by calling the
            object.
        """
        self.placeholder = placeholder

        # The "Hyperparameter Value Triology"
        self.db = HyperParameterDB()

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
                1. if `ast.literal_eval` returns without exception, the
                    the evaluated results are filled in the dict.
                2. otherwise a :class:`.primitives.NotLiteralEvaluable` sentinel object is
                    filled
        """
        source_helper = SourceHelper(source)

        root_node = ast.parse(source, filename)
        for node in ast.walk(root_node):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and (node.func.id == self.placeholder)
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
                    {
                        "name": name,
                        "value": value,
                        "filename": filename,
                        "lineno": lineno,
                        "ast_node": ast_node,
                        "hints": hints,
                        "priority": P.PRIORITY_PARSED_FROM_SOURCE_CODE,
                    }
                )
                self.db.push_occurrence(occ, source_helper=source_helper)

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

    def get_value(self, name: str, *, raise_exception: bool = True) -> object:
        """Get the authoritative value of a hyperparameter.
        Will raise an exception if value does not exist by default.

        :param hp_name: The name of the hyperparameter
        :param raise_exception: Defaults to True; set false to suppress
            exception. In this case, the missing value will be an instance
            of :class:`.primitives.EmptyValue`
        """
        v = self.db.select(lambda row: row.name == name).sorted(L.value_priority)
        if len(v) == 0:
            value = EmptyValue()
        else:
            value = v[0]["value"]

        if isinstance(value, EmptyValue) and raise_exception:
            raise KeyError("`{}` not found".format(name))
        return value

    def get_occurrence_of_value(self, name: str) -> Optional[HyperParameterOccurrence]:
        """
        :param hp_name: The name of the hyperparameter

        :return: a :class:`.hpm_db.HyperParameterOccurrence` object or None
        """

        s = self.db.select(L.of_name(name)).sorted(L.value_priority)
        return None if s.empty() else s[0]

    def get_values(self) -> dict:
        """Get all current available hyperparameters and their values.

        :return: dict of name to value.
        """

        # It is guaranteed to have at least one element using group_by
        return {
            k: d.sorted(L.value_priority)[0]["value"]
            for k, d in self.db.group_by("name").items()
        }

    def set_value(self, name: str, value: object) -> "HyperParameterManager":
        """Runtime setter. Set value with the highest priority.
        """
        self.db.push_occurrence(
            HyperParameterOccurrence(
                name=name, value=value, priority=P.PRIORITY_SET_FROM_SETTER
            )
        )
        return self

    def set_values(self, values: dict) -> "HyperParameterManager":
        """Runtime setter. Set a dict of values with the highest priority.
        """
        for k, v in values.items():
            self.set_value(k, v)
        return self

    def __call__(self, hp_name: str, hp_value: EmptyValue = EmptyValue(), **hints):
        """Runtime callable setter and getter. Will set the value with
        intermediate priority.
        """
        # TODO: record runtime meta-info (filename, lineno, etc.) as well
        # XXX: recording TOO MUCH in runtime may harm performance
        if not isinstance(hp_value, EmptyValue):
            self.db.push_occurrence(
                HyperParameterOccurrence(
                    name=hp_name, value=hp_value, priority=P.PRIORITY_SET_FROM_CALLABLE
                )
            )
        return self.get_value(hp_name)
