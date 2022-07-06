from dataclasses import dataclass
from typing import TypeVar, Generic

from persistable.io import DictEncodableMixin


ParamTypeT = TypeVar("ParamTypeT")


class PersistableParam(Generic[ParamTypeT]):

    """Parameter wrapper for parameters with special meta options such as being ignored from file hash."""

    def __init__(self, param: ParamTypeT, exclude_from_file_hash: bool = False) -> None:
        self.param = param
        self.exclude_from_file_hash = exclude_from_file_hash


@dataclass
class PersistableParams(DictEncodableMixin):
    def get_hash(self) -> str:
        ...
