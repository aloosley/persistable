from dataclasses import dataclass
from hashlib import md5
from typing import TypeVar, Generic

from persistable.io import DictEncodable

ParamTypeT = TypeVar("ParamTypeT")


class PersistableParam(Generic[ParamTypeT]):

    """Parameter wrapper for parameters with special meta options such as being ignored from file hash."""

    def __init__(self, param: ParamTypeT, exclude_from_file_hash: bool = False) -> None:
        self.param = param
        self.exclude_from_file_hash = exclude_from_file_hash


@dataclass
class PersistableParams(DictEncodable):
    def get_str_repr(self) -> str:
        return str(self.to_dict())

    def get_md5_hash(self) -> str:
        return md5(str(self).encode()).hexdigest()
