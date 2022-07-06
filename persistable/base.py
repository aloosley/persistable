from __future__ import annotations

import json
import re
from copy import deepcopy
from logging import WARNING, DEBUG, INFO, RootLogger
from pathlib import Path
from typing import Optional, Generic, Collection, Any, Dict

from .data import PersistableParams
from .exceptions import ExplainedNotImplementedError
from .io import FileIO, PickleFileIO, PayloadTypeT
from .persistload import PersistLoadBasic, PersistLoadWithParameters
from .util.dict import recdefaultdict, merge_dicts
from .util.logging import get_logger


def _camel_to_snake(name: str) -> str:
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class Persistable(Generic[PayloadTypeT]):
    def __init__(
        self,
        persistable_datadir: Path,
        params: PersistableParams,
        from_persistble_objs: Optional[Collection[Persistable]] = None,
        payload_name: Optional[str] = None,
        payload_io: Optional[FileIO[PayloadTypeT]] = None,
        payload_file_suffix: str = ".persistable",
        verbose: bool = False,
        logger: Optional[RootLogger] = None,
    ) -> None:
        if not persistable_datadir.is_dir():
            persistable_datadir.mkdir(parents=True)
        self.persistable_datadir = persistable_datadir
        self.params = params
        self.from_persistble_objs = from_persistble_objs
        if payload_name is None:
            payload_name = _camel_to_snake(self.__class__.__name__)
        self.payload_name = payload_name
        if payload_io is None:
            payload_io = PickleFileIO()
        self.payload_io = payload_io
        self.payload_file_suffix = payload_file_suffix

        console_level: INFO
        if verbose:
            console_level=INFO
        else:
            console_level=WARNING

        if logger is None:
            logger = get_logger(
                payload_name,
                file_loc=(persistable_datadir / f"{payload_name}.log"),
                file_level=DEBUG,
                console_level=console_level
            )

        self.logger = logger
        self.logger.info(f"---- NEW PERSISTABLE SESSION ---- ({persistable_datadir})")
        self.logger.info(f"Payload named {payload_name}; Parameters set to {params}")

        self._payload: Optional[PayloadTypeT] = None
        self._params_tree: Optional[PersistableParams] = None

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

        self.payload_io.save(payload=self._payload, filepath=self.persist_filepath.with_suffix(self.payload_file_suffix))
        with self.persist_filepath.with_suffix(".params.json").open("wb") as params_file_handler:
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
        return self._payload

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
        filename = "test"
        return self.persistable_datadir / filename


# Base classes
class PersistableOld:
    """
    A persistable logged object useful for ML use-cases.
    
    Basic instructions, inherit from Persistable:
    
    Features:
    LOGGER                                      - self.logger       (Logging)
    PERSISTABLE RECURSIVE DEFAULT DICTIONARY    - self.payload      (recdefaultdict by default, can be anything)
    PERSISTABLE PAYLOAD KEYS                    - self.payload_keys (dict_keys)
    PERSISTABLE PAYLOAD NAME                    - self.payload_name (str)
    PERSISTABLE TAGS                            - self.params       (dict)
    PERSIST/LOAD TOOLS                          - self.persistload  (PersistLoad)
    
    """

    def __init__(
        self, payload_name, params={}, required_params=tuple(), workingdatapath=None,
        persistloadtype="WithParameters", from_persistable_object=None,
        excluded_fn_params=[], verbose=True, dill=False
    ):
        """
        Generate a blank payload

        Parameters
        ----------
        payload_name            : str
            Name of the payload (for persisting purposes)
        params                  : dict
            Params describing the payload (these should uniquely define the payload of a given name)
        required_params         : list or tuple
            List of required parameters
        workingdatapath         : str or pathlib.Path
            The working directory, which is by default under the local-data directory, but can by overridden by
            passing a full pathlib.Path argument
        persistloadtype         : str
            Use either  Basic           - simple file names, no parameter tracking
                        WithParameters  - same as basic but with parameter tracking
        from_persistable_object : Persistable
            Construct a persistable object from another persistable object
        excluded_fn_params      : list
            Parameters to exclude from the file naming (usually because their values are too long for the name)
        verbose                 : bool
            Sets verbosity (True shows INFO level logs, False shows WARNING level logs)
        dill                    : bool
            Tells persist load to use dill instead of pickle.  This is useful if the user wants to trade 
            serialization speed (cPickle) for a more robust serializer (Dill)
        """

        # Either construct the persistable object from another persistable object,
        # or enforce that working_subdir and localdatapath are provided
        if from_persistable_object and isinstance(from_persistable_object, Persistable):
            workingdatapath = from_persistable_object.persistload.workingdatapath
            persistloadtype = from_persistable_object.persistload.get_type()
            params          = merge_dicts(
                params,
                {from_persistable_object.payload_name: from_persistable_object.fn_params}
            ) # ToDo: distinguish params from fn_params when constructing from an object
        elif from_persistable_object and isinstance(from_persistable_object, list):
            # ToDo: make this nicer
            workingdatapath = from_persistable_object[0].persistload.workingdatapath
            persistloadtype = from_persistable_object[0].persistload.get_type()
            params = merge_dicts(
                params,
                {
                    persistable_object.payload_name: persistable_object.fn_params
                    for persistable_object in from_persistable_object
                }
            )
        elif workingdatapath is None:
            raise ValueError("'workingdatapath' must be specified if not provided by another Persistable object")

        # Check params:
        self._validate_params(params=params)

        # Initialize payload:
        self.payload = recdefaultdict()

        # Save payload name and params:
        self.payload_name = payload_name
        self.params = params

        # Check required parameters:
        self._check_required_params(required_params)

        # Set filename parameters:
        self.fn_params = deepcopy(self.params)
        for param in excluded_fn_params:
            if param in self.fn_params:
                del self.fn_params[param]

        # Choose PersistLoad object type:
        if persistloadtype == "Basic":
            PersistLoadObj = PersistLoadBasic
        elif persistloadtype == "WithParameters":
            PersistLoadObj = PersistLoadWithParameters
        else:
            raise ValueError("persistloadtype currently only supports 'Basic' and 'WithParameters'")

        # Instantiate PersistLoad object:
        self.persistload = PersistLoadObj(workingdatapath, verbose=verbose, dill=dill)

        # Add a logger:
        # ToDo Improve logging control and output:
        class_name = self.__class__.__name__
        if verbose:
            console_level = INFO
        else:
            console_level = WARNING
        self.logger = get_logger(
            class_name,
            file_loc=(self.persistload.workingdatapath / f"{class_name}.log"),
            file_level=DEBUG,
            console_level=console_level
        )
        self.logger.info(f"---- NEW PERSISTABLE SESSION ---- ({self.persistload.workingdatapath})")
        self.logger.info(f"Payload named {self.payload_name}; Parameters set to {self.params}")

        # Save otherwise unsaved parameters to private variables:
        self._verbose = verbose
        self._persistloadtype = persistloadtype
        self._dill = dill

    def generate(self, persist=True, **untracked_payload_params):
        """
        Generates payload and (by default) persists it.
        
        Parameters
        ----------
        persist                     : bool
            Default True, the payload is persisted
        untracked_payload_params    : dict
            These are helper parameters for generating an object that are not tracked.  
            Generally these are not used.
        """
        self.logger.info(f"Now generating {self.payload_name} payload...")
        self._generate_payload(**untracked_payload_params)
        if persist:
            self.persist()

    def persist(self):
        """
        Persists the payload in it's current state.
        """



        self.persistload.persist(self.payload, self.payload_name, self.fn_params)

    def load(self, **untracked_payload_params):
        """
        Loads persisted payload
        
        Parameters
        ----------
        untracked_payload_params    : dict
            Parameters not tracked by persistable that are only used to run the _post_load.
            Such scripts are useful if part of the payload cannot be persisted and needs to be recalculated
            at load time.
        """
        self.logger.info(f"Now loading {self.payload_name} payload...")
        self.payload = self.persistload.load(self.payload_name, self.fn_params)
        self._post_load(**untracked_payload_params)

    def reset_payload(self):
        """
        Convenience function, useful if the user wants to load a payload and later remove it from memory.

        This can be useful when, for example, the user loads from a list of large persistables and only wants
        to keep one persistable payload in memory at a time.
        """
        del self.payload
        self.payload = recdefaultdict()

    def update_fn_params(self, new_fn_params: dict, delete_old: bool=True):
        """
        Updates fn_params (that uniquely define the payload along with the payload_name) and renames the persisted
        payload file accordingly.

        Convenience method when, during development, parameter names or values are refactored but the developer
        does not wishs to regenerate all her persistable payloads.

        Parameters
        ----------
        new_fn_params   : dict
            New fn_params to pin to the Persistable object.
        delete_old      : bool
            Use False to keep old parameterized payload file (sometimes useful for backwards compatibility).
            Use True to remove the old parameterized payload file (garbage collecting and storage friendly default).

        Returns
        -------

        """
        # Rename payload file:
        self.persistload.rename(
            self.payload_name, self.payload_name, self.fn_params, new_fn_params, delete_old=delete_old
        )

        # Update params:
        self.fn_params = new_fn_params

    def update_payload_name(self, new_payload_name: str, delete_old: bool=True):
        """
        Updates payload_name (that uniquely define the payload along with the fn_params) and renames the persisted
        payload file accordingly.

        Convenience method when, during development, parameter names or values are refactored but the developer
        does not wishs to regenerate all her persistable payloads.

        Parameters
        ----------
        new_payload_name    : str
            New payload_name to pin to the Persistable object
        delete_old          : bool
            Use False to keep old parameterized payload file (sometimes useful for backwards compatibility).
            Use True to remove the old parameterized payload file (garbage collecting and storage friendly default).

        Returns
        -------

        """
        # Rename payload file:
        self.persistload.rename(
            self.payload_name, new_payload_name, self.fn_params, self.fn_params, delete_old=delete_old
        )

        # Update params:
        self.payload_name = new_payload_name

    def load_generate(self, **untracked_payload_params):
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

    def _generate_payload(self, **untracked_payload_params):
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

        raise NotImplementedError("_generate_payload must be implemented by user")

    def _post_load(self, **untracked_payload_params):
        """
        Define here any extra algorithmic steps to run after loading the payload
        
        Parameters
        ----------
        untracked_payload_params    : dict
            Payload parameters that the user doesn't want to track (not persisted to file)

        Returns
        -------

        """

    def _check_required_params(self, list_of_required_params=tuple()):
        """
        A helper function for enforcing sets of minimal parameters passed by user.
        
        Parameters
        ----------
        list_of_required_params : list or tuple
            List of parameter names that must be provided in the params. 

        Returns
        -------

        """

        # Check if list_of_required_params is a list or tuple:
        if (not isinstance(list_of_required_params, list)) and (not isinstance(list_of_required_params, tuple)):
            # What to do when input is not a list or tuple:
            if isinstance(list_of_required_params, str):
                list_of_required_params = [list_of_required_params]
            else:
                raise ValueError(f"list_of_required_params must be of type tuple or list, "
                                 f"current it is {type(list_of_required_params)}")

        missing_params = []
        for required_param in list_of_required_params:
            if required_param not in self.params:
                missing_params += [required_param]

        if len(missing_params):
            raise ValueError(f"Some required parameters are missing: {missing_params}")

    def _validate_params(self, params):
        for key, value in params.items():
            if "/" in str(value):
                raise ValueError(f"Parameter {key} contained at least one '/', but this is not allowed.")


    def __getitem__(self, item):
        """
        For getting items more conveniently from the payload recdefaultdict
        
        Parameters
        ----------
        item    : key
            payload key

        Returns
        -------

        """
        if item in self.payload:
            return self.payload[item]
        else:
            raise KeyError(f"{item} not a payload key; keys include {self.payload.keys()}")

    @property
    def payload_keys(self):
        """
        Helper function to make accessing the payload easier
        
        Returns
        -------

        """

        if isinstance(self.payload, dict):
            return self.payload.keys()
        else:
            return None


class PersistableEnsemble:
    pass
