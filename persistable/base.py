from .util.logging import get_logger
from .util.dict import recdefaultdict, merge_dicts
from .persistload import PersistLoadBasic, PersistLoadWithParameters
from logging import WARNING, DEBUG, INFO
from copy import deepcopy


# Base classes
class Persistable:
    """
    A persistable logged object useful for ML use-cases.
    
    Basic instructions, inherit from Persistable:
    
    Features:
    LOGGER                                      - self.logger       (Logging)
    PERSISTABLE RECURSIVE DEFAULT DICTIONARY    - self.payload      (recdefaultdict)
    PERSISTABLE PAYLOAD NAME                    - self.payload_name (str)
    PERSISTABLE TAGS                            - self.params       (dict)
    PERSIST/LOAD TOOLS                          - self.persistload  (PersistLoad)
    
    """

    def __init__(
        self, payload_name, params={}, workingdatapath=None,
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
        working_subdir          : str or pathlib.Path
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
        if from_persistable_object:
            workingdatapath = from_persistable_object.persistload.workingdatapath
            persistloadtype = from_persistable_object.persistload.get_type()
            params          = merge_dicts(
                params,
                {from_persistable_object.payload_name: from_persistable_object.fn_params}
            ) # ToDo: distinguish params from fn_params when constructing from an object
        elif workingdatapath is None:
            raise ValueError("'workingdatapath' must be specified if not provided by another Persistable object")

        # Initialize payload:
        self.payload = recdefaultdict()

        # Save payload name and params:
        self.payload_name = payload_name
        self.params = params

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
            console_level=INFO
        else:
            console_level=WARNING
        self.logger = get_logger(
            class_name,
            file_loc=(self.persistload.workingdatapath / f"{class_name}.log"),
            file_level=DEBUG,
            console_level=console_level
        )
        self.logger.info(f"---- NEW PERSISTABLE SESSION ---- ({self.persistload.workingdatapath})")
        self.logger.info(f"Payload named {self.payload_name}; Parameters set to {self.params}")

    def generate(self, persist=True, **untracked_payload_params):
        """
        Generates payload and (by default) persist it.
        
        Parameters
        ----------
        persist                     : bool
            Default True, the payload is persisted
        untracked_payload_params    : dict
            These are helper parameters for generating an object that should not be tracked.  
            Generally these are not used.

        Returns
        -------

        """
        self.logger.info(f"Now generating {self.payload_name} payload...")
        self._generate_payload(**untracked_payload_params)
        if persist:
            self.persistload.persist(self.payload, self.payload_name, self.fn_params)

    def load(self):
        """
        Loads persisted payload
        
        Returns
        -------

        """
        self.logger.info(f"Now loading {self.payload_name} payload...")
        self.payload = self.persistload.load(self.payload_name, self.fn_params)

    def _generate_payload(self, **untracked_payload_params):
        """
        Define here the algorithm for generating the payload
        based on self.params
        
        Returns
        -------
        """

        raise NotImplementedError("_generate_payload must be implemented by user")

    def _check_required_params(self, list_of_required_params=[]):
        """
        A helper function for enforcing sets of minimal parameters passed by user.
        
        Parameters
        ----------
        list_of_required_params : list
            List of parameter names that must be provided in the params. 

        Returns
        -------

        """

        missing_params = []
        for required_param in list_of_required_params:
            if required_param not in self.params:
                missing_params += [required_param]

        if len(missing_params):
            raise ValueError(f"Some required parameters are missing: {missing_params}")
