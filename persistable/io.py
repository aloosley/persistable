import pickle
from abc import ABC, abstractmethod
from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import TypeVar, Generic, Any, cast, Dict, Type, Set, Callable

import numpy as np

from persistable.exceptions import ExplainedNotImplementedError

PayloadTypeT = TypeVar("PayloadTypeT")


logger = getLogger(__name__)


class FileIO(Generic[PayloadTypeT], ABC):

    """FileIO Abstraction with load / save interface."""

    def load(self, filepath: Path, **kwargs: Any) -> PayloadTypeT:
        logger.debug("load `%s`", filepath)
        return self._load(filepath=filepath, **kwargs)

    def save(self, payload: PayloadTypeT, filepath: Path, create_folder: bool = True, **kwargs: Any) -> None:
        logger.debug("save %s to `%s`", payload.__class__.__name__, filepath)
        try:
            if create_folder and not filepath.parent.is_dir():
                filepath.parent.mkdir(parents=True)
            self._save(payload=payload, filepath=filepath, **kwargs)
        except Exception as exception:
            raise IOError(f"{payload.__class__.__name__} unable to save to `{filepath}`") from exception

    @abstractmethod
    def _load(self, filepath: Path, **kwargs: Any) -> PayloadTypeT:
        """Specific load from file implementation."""

    def _save(self, payload: PayloadTypeT, filepath: Path, **kwargs: Any) -> None:
        """Specific save to file implementation."""
        raise ExplainedNotImplementedError(self._save.__name__)


class PickleFileIO(FileIO[PayloadTypeT], Generic[PayloadTypeT]):
    def _load(self, filepath: Path, **kwargs: Any) -> PayloadTypeT:
        with filepath.open("rb") as file_handler:
            return cast(PayloadTypeT, pickle.load(file=file_handler, **kwargs))

    def _save(self, payload: PayloadTypeT, filepath: Path, **kwargs: Any) -> None:
        with filepath.open("wb") as file_handler:
            pickle.dump(obj=payload, file=file_handler, **kwargs)


class DictEncodable:

    """Mixin for encoding a python object to a dict.

    By default, this mixin will stringify Path and Enum objects.  To define more type based encoding methods, or
    override default behaviour, override the `_custom_type_encoder_map` property.
    """

    def to_dict(self) -> Dict[str, Any]:

        """Get a dictionary representation of self."""

        encoded_dict: Dict[str, Any] = dict()
        exluded_attributes = self._excluded_attributes
        custom_type_encoder_map = self._custom_type_encoder_map
        for attr_name, attr in self.__dict__.items():
            if attr_name in exluded_attributes:
                continue
            elif isinstance(attr, tuple(custom_type_encoder_map)):
                subclass_found_in_extra_dict_encodings: Type[Any] = [
                    class_ for class_ in attr.__class__.mro() if class_ in custom_type_encoder_map
                ][0]
                encoded_dict[attr_name] = custom_type_encoder_map[subclass_found_in_extra_dict_encodings](attr)
            elif isinstance(attr, Path):
                encoded_dict[attr_name] = str(attr)
            elif isinstance(attr, Enum):
                encoded_dict[attr_name] = attr.name
            elif isinstance(attr, DictEncodable):
                encoded_dict[attr_name] = attr.to_dict()
            else:
                encoded_dict[attr_name] = attr
        return encoded_dict

    @property
    def _excluded_attributes(self) -> Set[str]:
        """
        Define a set of self.__dict__ attributes that should be excluded from the dict encoder.

        For example, the self.__dict__ of a dataclass has an internal attribute `__initialised__`.  This is excluded
        by default.
        """
        return {
            "__initialised__",
        }

    @property
    def _custom_type_encoder_map(self) -> Dict[Type[Any], Callable[[Any], Any]]:
        """
        Define how attributes with certain types get mapped to dict.

        Note, this map also overrides default behaviour.

        Example:
            Override how Path objects are encoded (in this case, change "/" to "!_!"):
            >>> from pathlib import Path
            >>> return {
            >>>     Path: lambda path: str(path).replace("/", "!_!")
            >>> }
        """
        return dict()

    @staticmethod
    def dict_almost_equal(
        dict1: Dict[Any, Any],
        dict2: Dict[Any, Any],
        rtol: float = 1e-6,
        atol: float = 1e-6,
        verbose: bool = False,
    ) -> bool:
        if dict1.keys() != dict2.keys():
            return False

        msg = "{}: {}!={} (rtol={}, atol={})"
        for key, value in dict1.items():
            if isinstance(value, dict):
                if DictEncodable.dict_almost_equal(dict1[key], dict2[key], rtol=rtol, atol=atol):
                    continue
                else:
                    print(msg.format(key, dict1[key], dict2[key], rtol, atol)) if verbose else None
                    return False

            if isinstance(value, float):
                if cast(bool, np.isclose(dict1[key], dict2[key], rtol=rtol, atol=atol, equal_nan=True)):
                    continue
                else:
                    print(msg.format(key, dict1[key], dict2[key], rtol, atol)) if verbose else None
                    return False

            if isinstance(value, np.ndarray):
                if np.allclose(dict1[key], dict2[key], atol=atol, rtol=rtol):
                    continue
                else:
                    print(msg.format(key, dict1[key], dict2[key], rtol, atol)) if verbose else None
                    return False

            if dict1[key] == dict2[key]:
                continue

            print(msg.format(key, dict1[key], dict2[key], rtol, atol)) if verbose else None
            return False

        return True
