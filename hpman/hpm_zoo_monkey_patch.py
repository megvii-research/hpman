from types import ModuleType
from typing import Dict, List

from .hpm import HyperParameterManager

hpm_zoo = {}  # type: Dict[str, HyperParameterManager]


class HPMZooModule(ModuleType):
    """The module-hack that allows us to use ``from hpman.m import
    some_program``. This hack is prviously used by plumbum."""

    __all__ = ()  # to make help() happy
    __package__ == __name__

    def __getattr__(self, name):
        if name in hpm_zoo:
            return hpm_zoo[name]
        hpm_zoo[name] = HyperParameterManager(name)
        return hpm_zoo[name]

    __path__ = []  # type: List[str]
    __file__ = __file__
