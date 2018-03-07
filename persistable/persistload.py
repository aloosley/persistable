from .util.logging import get_logger
from .util.os_util import default_standard_filename, parse_standard_filename, handle_long_fn
from .util.dict import recursive_value_map
from logging import INFO, WARNING
import pickle as cpickle
import dill as dpickle

class PersistLoad:
    def __init__(self, workingdatapath, verbose=True, dill=False):
        """
        :param workingdatapath: pathlib.Path
            - working sub-directory name under the LOCALDATAPATH to/from which to save/load local data
            - can override the entire absolute directory using a corresponding pathlib.Path object
        """

        # Set local data path, create folder if it doesn't exist:
        self.workingdatapath = workingdatapath
        if not self.workingdatapath.exists():
            self.workingdatapath.mkdir()

        # Get persistload logger:
        if verbose:
            console_level=INFO
        else:
            console_level=WARNING
        self.logger = get_logger(self.__class__.__name__, console_level=console_level)

        # Reference to Serializer:
        if dill:
            self.serializer = dpickle
        else:
            self.serializer = cpickle

    def persist(self, obj, fn_type):
        raise NotImplementedError("persist must be implemented")

    def load(self, fn_type):
        raise NotImplementedError("load must be implemented")

    def get_type(self):
        return self.__class__.__name__.split("PersistLoad")[-1]


class PersistLoadBasic(PersistLoad):
    def __init__(self, workingdatapath, verbose=True, dill=False):
        super().__init__(workingdatapath, verbose=verbose, dill=dill)

    def persist(self, obj, fn_type):
        self.logger.info(f"PERSISTING {fn_type}")
        with open(self.workingdatapath / f"{fn_type}.pkl", 'wb') as f:
            self.serializer.dump(obj, f)

    def load(self, fn_type):
        self.logger.info(f"LOADING {fn_type}")
        with open(self.workingdatapath / f"{fn_type}.pkl", 'rb') as f:
            return self.serializer.load(f)


class PersistLoadWithParameters(PersistLoad):

    def __init__(self, workingdatapath, verbose=True, dill=False):
        super().__init__(workingdatapath, verbose=verbose, dill=dill)

    def persist(self, obj, fn_type, fn_params={}, fn_ext=None):

        # Get filename:
        fn = default_standard_filename(fn_type, fn_ext=fn_ext, **fn_params)

        # Persist with handling for long filenames
        # (which aren't always supported depending on the OS):
        self._persist_with_params(fn, fn_type, obj)


    def load(self, fn_type, fn_params={}, fn_ext=None):

        # Get filename:
        fn = default_standard_filename(fn_type, fn_ext=fn_ext, **fn_params)
        self.logger.info("Attempting to LOAD %s from:\n <--- %s --->" % (fn_type, fn))

        return self._load_with_params(fn, fn_type, fn_params)

    def _load_similar_file(self, fn_type, fn_params):

        similar_filepaths = self._find_similar_files(fn_type, fn_params)

        if len(similar_filepaths) == 1:
            self.logger.warning("Found similar file in path, loading: \n <--- %s --->" % similar_filepaths[0])
            with open(similar_filepaths[0], 'rb') as f:
                return self.serializer.load(f)

        elif len(similar_filepaths) > 1:
            notice = "Not enough parameters specified, found more than one related model: %s" % similar_filepaths
            self.logger.fatal(notice)
            raise FileNotFoundError(notice)

        else:
            self.logger.warning("No similar %s file in path... " % fn_type)
            raise FileNotFoundError("No similar models found")

    def _find_similar_files(self, fn_type, fn_params):
        """
        The goal of this helper is to find files with file_fn_params such that fn_param is a subset of file_fn_params

        Parameters
        ----------
        fn_type     : str
        fn_params   : dict

        Returns
        -------

        """


        # Check all files for similar files:
        similar_files = []
        # fn_params = recursive_key_map(lambda k: SHORTEN_PARAM_MAP.get(k,k), fn_params, factory=dict)
        compare_fn_dict = recursive_value_map(lambda val: repr(val).replace(" ", ""), fn_params)
        for filepath in self.workingdatapath.glob('*'):

            # Get filename:
            fn = filepath.name

            # Parse filename, get model parameters:
            file_fn_type, _, file_fn_dict = parse_standard_filename(fn)

            # Skip if file_kind not equivalent:
            if fn_type != file_fn_type:
                continue

            # Note all files where compare_fn_dict is a subset of file_fn_params:
            try:
                if all(file_fn_dict[k] == compare_fn_dict[k] for k in compare_fn_dict):
                    similar_files.append(filepath)
            except KeyError:
                continue

        return similar_files

    def _persist_with_params(self, fn, fn_type, obj):

        # Check if a filename is too long:
        is_longfilename, modified_filenames = handle_long_fn(fn, fn_type)
        fn_topersist = modified_filenames[0]

        if is_longfilename:
            self.logger.info("Filename too long to save, compressing name...")

        # Persist the pkl file:
        self.logger.info("PERSISTING %s to:\n ---> %s <---" % (fn_type, fn_topersist))

        # Persist:
        # patched_pickle_dump(obj, os.path.join(self.local_save_dir, fn_topersist))
        with open(self.workingdatapath / fn_topersist, 'wb') as f:
            self.serializer.dump(obj, f)

        # Add parameters text if fn length > 255:
        if is_longfilename:
            self.logger.info("Saving params to txt-file:\n ---> %s <---" % modified_filenames[1])

            # Persist parameters to txt file:
            with open(self.workingdatapath / modified_filenames[1], 'w') as f:
                f.write(fn)

    def _load_with_params(self, fn, fn_type, fn_params):

        # Check if a filename is too long:
        is_longfilename, modified_filenames = handle_long_fn(fn, fn_type)
        fn_toload = modified_filenames[0]

        if is_longfilename:
            self.logger.info(
                "Filename too long, searching for compressed version instead: \n <--- %s --->" % fn_toload
            )

        # First attempt to find exact file:
        try:
            # load_obj = patched_pickle_load(os.path.join(self.local_save_dir, fn_toload))
            with open(self.workingdatapath / fn_toload, 'rb') as f:
                load_obj = self.serializer.load(f)
            self.logger.info("Exact %s file found and LOADED!" % fn_type)
            return load_obj

        # If no exact file, find similar file:
        # (Useful when not all parameters exactly specified):
        except FileNotFoundError:
            load_obj = self._load_similar_file(
                fn_type=fn_type, fn_params=fn_params
            )  # Raises an FileNotFound exception if fails
            self.logger.info("Similar %s file found and LOADED!" % fn_type)
            return load_obj