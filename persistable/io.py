import pickle
from abc import ABC, abstractmethod
from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import TypeVar, Generic, Any, cast, Dict, Type, Set, Callable

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


class DictEncodableMixin:
    """ Mixin for encoding a python object to a dict that can be used for yaml or json. """

    def to_dict(self) -> Dict[str, Any]:
        """ Get dictionary representation of this object that can be serialized by a JSONEncoder """
        encoded_dict: Dict[str, Any] = dict()
        attributes_to_skip = self._dict_encoding_filters
        extra_dict_encodings = self._extra_dict_encodings
        for attr_name, attr in self.__dict__.items():
            if attr_name in attributes_to_skip:
                continue

            elif isinstance(attr, Enum):
                encoded_dict[attr_name] = attr.name
            elif isinstance(attr, tuple(extra_dict_encodings)):
                subclass_found_in_extra_dict_encodings: Type[Any] = [
                    class_ for class_ in attr.__class__.mro() if class_ in extra_dict_encodings
                ][0]
                encoded_dict[attr_name] = extra_dict_encodings[subclass_found_in_extra_dict_encodings](attr)
            elif isinstance(attr, DictEncodableMixin):
                encoded_dict[attr_name] = attr.to_dict()
            else:
                encoded_dict[attr_name] = attr
        return encoded_dict

    @property
    def _dict_encoding_filters(self) -> Set[str]:
        """Set of dataclass attributes not to encode to dict."""
        return {
            "__initialised__",
        }

    @property
    def _extra_dict_encodings(self) -> Dict[Type[Any], Callable[[Any], Any]]:
        """Override with specific encoding callables.

        Examples:
            Encode path objects to string:
            >>> from pathlib import Path
            >>> return {
            >>>     Path: lambda path: str(path)
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
                if DictEncodableMixin.dict_almost_equal(dict1[key], dict2[key], rtol=rtol, atol=atol):
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

            if dict1[key] == dict2[key]:
                continue

            print(msg.format(key, dict1[key], dict2[key], rtol, atol)) if verbose else None
            return False

        return True