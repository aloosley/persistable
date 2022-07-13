from __future__ import annotations

import json
import re
from hashlib import md5
from logging import WARNING, DEBUG, INFO, Logger
from pathlib import Path
from typing import Optional, Generic, Collection, Any, Dict, cast, TypeVar

from persistable.data import PersistableParams
from persistable.exceptions import ExplainedNotImplementedError
from persistable.io import FileIO, PickleFileIO, PayloadTypeT
from persistable.logging import get_logger


def _camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


PersistableParamsT = TypeVar("PersistableParamsT", bound=PersistableParams)


class Persistable(Generic[PayloadTypeT, PersistableParamsT]):
    def __init__(
        self,
        persist_data_dir: Path,
        params: PersistableParamsT,
        *,
        from_persistble_objs: Optional[Collection[Persistable[Any, Any]]] = None,
        payload_name: Optional[str] = None,
        payload_io: Optional[FileIO[PayloadTypeT]] = None,
        payload_file_suffix: str = ".persistable",
        verbose: bool = False,
        logger: Optional[Logger] = None,
    ) -> None:
        if not persist_data_dir.is_dir():
            persist_data_dir.mkdir(parents=True)
        self.persist_data_dir = persist_data_dir
        self.params = params
        if from_persistble_objs is None:
            from_persistble_objs = []
        self.from_persistble_objs = from_persistble_objs
        if payload_name is None:
            payload_name = _camel_to_snake(self.__class__.__name__)
        self.payload_name = payload_name
        if payload_io is None:
            payload_io = PickleFileIO()
        self.payload_io = payload_io
        self.payload_file_suffix = payload_file_suffix

        console_level: int
        if verbose:
            console_level = INFO
        else:
            console_level = WARNING

        if logger is None:
            logger = get_logger(
                payload_name,
                file_loc=persist_data_dir / f"{payload_name}.log",
                file_level=DEBUG,
                console_level=console_level,
            )

        self.logger = logger
        self.logger.info(f"---- NEW PERSISTABLE SESSION ---- ({persist_data_dir})")
        self.logger.info(f"Payload named {payload_name}; Parameters set to {params}")

        self._payload: Optional[PayloadTypeT] = None
        self._params_tree: Optional[Dict[str, Any]] = None

    @property
    def params_tree(self) -> Dict[str, Any]:
        if self._params_tree is None:
            self._params_tree = self.params.to_dict() | {
                persistable_obj.payload_name: persistable_obj.params.to_dict()
                for persistable_obj in self.from_persistble_objs
            }

        return self._params_tree

    def generate(self, persist: bool = True, **untracked_payload_params: Any) -> None:
        """
        Generates payload and (by default) persist it.

        Parameters
        ----------
        persist                     : bool
            Default True, the payload is persisted
        untracked_payload_params    : dict
            These are helper parameters for generating an object that are not tracked.
            Generally these are not used.

        Returns
        -------

        """
        self.logger.info(f"Now generating {self.payload_name} payload...")
        self._payload = self._generate_payload(**untracked_payload_params)
        if persist:
            self.persist()

    def persist(self) -> None:

        """Persist both payload and parameters."""

        if self._payload is None:
            raise ValueError("Payload has not been generated.")

        self.payload_io.save(
            payload=self._payload,
            filepath=self.persist_filepath.with_suffix(self.payload_file_suffix),
        )
        with self.persist_filepath.with_suffix(".params.json").open("w") as params_file_handler:
            json.dump(self.params_tree, params_file_handler)

    def load(self, **untracked_payload_params: Any) -> None:
        """
        Loads persisted payload

        Parameters
        ----------
        untracked_payload_params    : dict
            Parameters not tracked by persistable that are only used to run the _post_load.
            Such scripts are useful if part of the payload cannot be persisted and needs to be recalculated
            at load time.

        Returns
        -------

        """
        self.logger.info(f"Now loading {self.payload_name} payload...")
        # ToDo - add find similar file functionality
        self._payload = self.payload_io.load(self.persist_filepath.with_suffix(self.payload_file_suffix))
        self._post_load()

    def load_generate(self, **untracked_payload_params: Any) -> None:
        """
        Like load() but executes the generate() method if load() fails due to a FileNotFoundError.

        Returns
        -------

        """
        try:
            self.load(**untracked_payload_params)
        except FileNotFoundError:
            self.logger.info("Loading payload failed, continuing to generate payload...")
            self.generate(**untracked_payload_params)

    @property
    def payload(self) -> PayloadTypeT:
        if self._payload is None:
            self.load_generate()
        return cast(PayloadTypeT, self._payload)

    def reset_payload(self) -> None:
        self._payload = None

    def _generate_payload(self, **untracked_payload_params: Any) -> PayloadTypeT:
        """
        Define here the algorithm for generating the payload
        based on self.params

        Parameters
        ----------
        untracked_payload_params    : dict
            Payload parameters that the user doesn't want to track (not persisted to file)

        Returns
        -------
        """

        raise ExplainedNotImplementedError(method_name=self._generate_payload.__name__)

    def _post_load(self) -> None:
        """
        Define here extra algorithmic steps to run after loading the payload.

        This is sometimes useful to add back components of the payload that are inefficient to persist or
        should not be persisted.

        Parameters
        ----------
        untracked_payload_params    : dict
            Payload parameters that the user doesn't want to track (not persisted to file)

        Returns
        -------

        """

    @property
    def persist_filepath(self) -> Path:
        filename = md5(str(self.params_tree).encode()).hexdigest()
        return self.persist_data_dir / filename
