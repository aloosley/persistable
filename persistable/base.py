from __future__ import annotations

import json
import re
import warnings
from hashlib import md5
from logging import WARNING, DEBUG, INFO, Logger
from pathlib import Path
from typing import Optional, Generic, Any, Dict, cast, TypeVar, Iterable

from persistable.data import PersistableParams
from persistable.exceptions import ExplainedNotImplementedError, NoPayloadError, InvalidPayloadWarning
from persistable.io import FileIO, PickleFileIO, PayloadTypeT
from persistable.logging import get_logger


def _camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


PersistableParamsT = TypeVar("PersistableParamsT", bound=PersistableParams)


class Persistable(Generic[PayloadTypeT, PersistableParamsT]):
    """
    A payload wrapper for simple parameter based generation, persisting, and loading.

    The Persistable class is the centerpiece of a lightweight framework for quickly developing data and model pipelines.
    Pipelines are clearly parameterized, and parameter based persisting and loading means you'll never lose track of
    your results.  If you already ran a long running persistable pipline (i.e. generated a persistable payload), it can
    be reloaded with ease so it doesn't have to run again unless you explicitly want it to.
    """

    def __init__(
        self,
        data_dir: Path,
        params: PersistableParamsT,
        tracked_persistable_dependencies: Optional[Iterable[Persistable[Any, Any]]],
        *,
        payload_name: Optional[str] = None,
        payload_io: Optional[FileIO[PayloadTypeT]] = None,
        payload_file_suffix: str = ".persistable",
        verbose: bool = False,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Contstructor

        Args:
            data_dir (Path): Directory where persistable payloads will be persisted to and/or loaded from.
            params (PersistableParamsT): Parameters defining the pipeline and parameter based persisting and loading.
                These should be a dataclass like object that inherits from PersistableParams.
            tracked_persistable_dependencies (Optional[Iterable[Persistable[Any, Any]]]): Persistable dependencies with
                parameters that should be tracked for the purpose of persisting and loading.  If the payload depends on
                access to other persistable payloads (regardless of if they've been generated or loaded), those
                persistable objects should be provided here.  Otherwise pass None.
            payload_name (Optional[str]): Name the payload.  Useful for recognizing persisted data-files and log-files.
                For the purpose of parameter base persisting and loading, the payload_name is also used.  When no
                payload_name is provided, the Persistable class-name in camel-case is used.
            payload_io (Optional[FileIO[PayloadTypeT]]): IO with input
            payload_file_suffix ():
            verbose ():
            logger ():
        """
        if not data_dir.is_dir():
            data_dir.mkdir(parents=True)
        self.data_dir = data_dir
        self.params = params
        if tracked_persistable_dependencies is None:
            tracked_persistable_dependencies = []
        self.tracked_persistable_dependencies = tracked_persistable_dependencies
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
                file_loc=data_dir / f"{payload_name}.log",
                file_level=DEBUG,
                console_level=console_level,
            )

        self.logger = logger
        self.logger.info(f"---- NEW PERSISTABLE SESSION ---- ({data_dir})")
        self.logger.info(f"Payload named {payload_name}; Parameters set to {params}")

        self._payload: Optional[PayloadTypeT] = None

    @property
    def params_tree(self) -> Dict[str, Any]:
        return self.params.to_dict() | {
            persistable_obj.payload_name: persistable_obj.params_tree
            for persistable_obj in self.tracked_persistable_dependencies
        }

    def generate(self, persist: bool = True, **untracked_payload_params: Any) -> None:
        """
        Generate payload and (by default) persist it.

        This method requires an implementation of _generate_payload().

        Parameters
        ----------
        persist                     : bool
            Default True, the payload is persisted
        untracked_payload_params    : dict
            These are helper parameters for generating an object that are not tracked.
            Generally these are not used.


        """
        self.logger.info(f"Now generating {self.payload_name} payload...")
        generated_payload = self._generate_payload(**untracked_payload_params)
        self._validate_payload(payload=generated_payload)
        self._payload = generated_payload
        if persist:
            self.persist()

    def persist(self) -> None:

        """Persist both payload and parameters."""

        if self._payload is None:
            raise ValueError("Payload has not been generated.")

        payload_filepath = self.persist_filepath.with_suffix(self.payload_file_suffix)
        params_filepath = self.persist_filepath.with_suffix(".params.json")

        self.payload_io.save(payload=self._payload, filepath=payload_filepath)
        with params_filepath.open("w") as params_file_handler:
            json.dump(self.params_tree, params_file_handler)
        self.logger.info(
            f"Successfully persisted payload to {payload_filepath.name} "
            f"(see {params_filepath.name} to view corresponding params)."
        )

    def load(self, warn_if_validation_fails: bool = False, **untracked_payload_params: Any) -> None:
        """
        Loads persisted payload

        Parameters
        ----------
        warn_if_validation_fails    : bool
            Use True to catch exceptions from valid_payload and throw a warning instead.
        untracked_payload_params    : dict
            Parameters not tracked by persistable that are only used to run the _post_load.
            Such scripts are useful if part of the payload cannot be persisted and needs to be recalculated
            at load time.

        Returns
        -------

        """
        self.logger.info(f"Now loading {self.payload_name} payload...")
        # ToDo - add find similar file functionality

        payload_filepath = self.persist_filepath.with_suffix(self.payload_file_suffix)
        loaded_payload = self.payload_io.load(filepath=payload_filepath)

        try:
            self._validate_payload(loaded_payload)
        except Exception as exception:
            if warn_if_validation_fails:
                warning_message = "Loaded payload was invalid (it may need to be regenerated)"
                warnings.warn(message=warning_message, category=InvalidPayloadWarning)
                self.logger.warning(msg=warning_message, exc_info=exception)
            else:
                raise exception

        self._payload = loaded_payload
        self.logger.info(f"Successfully loaded payload from {payload_filepath.name}")

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

    def validate_payload(self, payload: Optional[PayloadTypeT] = None) -> None:
        """
        Validate the payload.

        This method requires an implementation of _validate_payload(), which should error if the payload is invalid.
        """
        if payload is None:
            if self._payload is None:
                raise NoPayloadError("Method validate_payload() was called, but there is no payload to validate.")
            payload = self._payload
        self.logger.info("Validating payload...")
        self._validate_payload(payload)
        self.logger.info("Payload validated!")

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

    def _validate_payload(self, payload: PayloadTypeT) -> None:
        """
        Define here checks to ensure the payload is valid.

        For example, a check could be that the payload is a table with five columns.

        Parameters
        ----------
        payload    : PayloadTypeT
            Payload to validate

        Returns
        -------
        """

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
        params_tree_hex = md5(str({self.payload_name: self.params_tree}).encode()).hexdigest()
        return self.data_dir / f"{self.payload_name}({params_tree_hex})"
