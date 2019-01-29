from .util.logging import get_logger
from .util.os_util import default_standard_filename, parse_standard_filename, handle_long_fn, _fn_to_paramsfn
from .util.dict import recursive_value_map
from pyparsing import ParseException
from tqdm import tqdm
from logging import INFO, WARNING
from typing import Tuple
from shutil import copyfile
import pickle as cpickle
import dill as dpickle
import warnings


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
            self.workingdatapath.mkdir(parents=True)

        # Get persistload logger:
        if verbose:
            console_level = INFO
        else:
            console_level = WARNING
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

        # Get suitable filename (i.e. handling long fns that aren't always supported by Windows):
        payload_fn, original_fn, is_hashed = self.get_fn(fn_type=fn_type, fn_params=fn_params, fn_ext=fn_ext)

        # Persist the pkl file:
        self.logger.info("PERSISTING %s to:\n ---> %s <---" % (fn_type, payload_fn))

        # Persist:
        with open(self.workingdatapath / payload_fn, 'wb') as f:
            self.serializer.dump(obj, f)

        # Add parameters text if fn length > 255:
        if is_hashed:
            params_fn = _fn_to_paramsfn(payload_fn)

            self.logger.info("Saving params to txt-file:\n ---> %s <---" % params_fn)

            # Persist parameters to txt file:
            with open(self.workingdatapath / params_fn, 'w') as f:
                f.write(original_fn)

    def load(self, fn_type, fn_params={}, fn_ext=None):
        # Get suitable filename (i.e. handling long fns that aren't always supported by Windows):
        payload_fn, unhashed_fn, is_hashed = self.get_fn(fn_type=fn_type, fn_params=fn_params, fn_ext=fn_ext)

        self.logger.info(f"Attempting to LOAD {fn_type} from:\n <--- {payload_fn} --->")
        return self._load_helper(payload_fn, unhashed_fn, fn_type, fn_params)

    def rename(self, old_fn_type, new_fn_type, old_fn_params, new_fn_params, fn_ext=None, delete_old=True):
        """
        Renames payload file based on old fn_params to payload file based on new fn_params

        Parameters
        ----------
        old_fn_type
        old_fn_params
        new_fn_params
        fn_ext
        delete_old

        Returns
        -------

        """
        # Skip trivial case:
        if (old_fn_params==new_fn_params) and (old_fn_type==new_fn_type):
            self.logger.info("Parameters are equivalent to before, no update made.")
            return

        # Get filenames:
        payload_fn_old, _, is_hashed_old = self.get_fn(
            fn_type=old_fn_type, fn_params=old_fn_params, fn_ext=fn_ext
        )
        payload_fn_new, original_fn_new, is_hashed_new = self.get_fn(
            fn_type=new_fn_type, fn_params=new_fn_params, fn_ext=fn_ext
        )

        # Get filepaths:
        oldfilepath = self.workingdatapath / payload_fn_old
        newfilepath = self.workingdatapath / payload_fn_new

        # Stop if new file already exists:
        if newfilepath.exists():
            raise FileExistsError(f"'{payload_fn_new}' already exists, parameter renaming aborted")

        # Copy or Rename:
        if delete_old:
            self.logger.info(f"Renaming: \n ---x {payload_fn_old} x--- \nto\n ---> {payload_fn_new} <---")
            oldfilepath.rename(newfilepath)
        else:
            self.logger.info(f"Copying: \n ---- {payload_fn_old} ---- \nto\n ---> {payload_fn_new} <---")
            copyfile(oldfilepath, newfilepath)

        # Remove old params-file (if exists and if delete_old flagged):
        if is_hashed_old and delete_old:
            # Removing old file (unlink):
            params_fn_old = _fn_to_paramsfn(payload_fn_old)
            self.logger.info(f"Deleting {params_fn_old}")
            (self.workingdatapath / params_fn_old).unlink()

        # Add new params-file
        if is_hashed_new:
            # Persist parameters to txt file:
            params_fn_new = _fn_to_paramsfn(payload_fn_new)
            self.logger.info("Saving params to txt-file:\n ---> %s <---" % params_fn_new)
            with open(self.workingdatapath / params_fn_new, 'w') as f:
                f.write(original_fn_new)

    def get_fn(self, fn_type: str, fn_params: dict={}, fn_ext: str=None) -> Tuple[str, str, bool]:
        """
        Get filename and info based on type, params, and extension

        Parameters
        ----------
        fn_type     : str
        fn_params   : dict
        fn_ext      : str or None

        Returns
        -------
        """
        # Get standard filename:
        original_fn = default_standard_filename(fn_type, fn_ext=fn_ext, **fn_params)

        # Handle long filename problems with Windows:
        is_hashed, payload_fn, params_fn = handle_long_fn(
            fn=original_fn, fn_type=fn_type, workingdatapath=self.workingdatapath
        )

        if is_hashed:
            self.logger.info(
                f'Long filename detected. It was hashed from \n"{original_fn}"\nto\n"{payload_fn}"\n'
                f'to avoid errors with Windows systems.')

        return payload_fn, original_fn, is_hashed

    def _load_helper(self, payload_fn: str, unhashed_fn: str, fn_type: str, fn_params: dict):
        """
        Load helper covers error handling when file loading goes wrong, including looking
        for similar persistable files and unhashed versions.

        Parameters
        ----------
        payload_fn  : str
            payload filename to load (potentially hashed)
        unhashed_fn : str
            unhashed payload filename (may be same as payload fn)
        fn_type     : str
            same variable defined at api level
        fn_params   : dict
            same variable defined at api level

        Returns
        -------

        """
        # First attempt to find exact file:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with open(self.workingdatapath / payload_fn, 'rb') as f:
                    load_obj = self.serializer.load(f)
            self.logger.info("Exact %s file found and LOADED!" % fn_type)

        # If no exact file, find similar file or fallback (for backwards compatibility):
        # (Useful when not all parameters exactly specified):
        except FileNotFoundError:
            try:
                # Try to load original filename (for backwards compatibility):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    with open(self.workingdatapath / unhashed_fn, 'rb') as f:
                        load_obj = self.serializer.load(f) # Raises an FileNotFoundError exception if fails
                    self.logger.info(f"Unhashed {fn_type} file found and LOADED")
            except FileNotFoundError:
                load_obj = self._load_similar_file(
                    fn_type=fn_type, fn_params=fn_params
                )
                self.logger.info(f"Similar {fn_type} file found and LOADED!")

        # Provide load_obj
        return load_obj

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

    def _find_similar_files(self, fn_type: str, fn_params: dict) -> list:
        """
        The goal of this helper is to find files with file_fn_params such that fn_param is a subset of file_fn_params

        Parameters
        ----------
        fn_type         : str
            same variable defined at api level
        fn_params       : dict
            same variable defined at api level

        Returns
        -------
        similar_files   : list

        """

        # Check all files for similar files:
        similar_files = []

        # fn_params = recursive_key_map(lambda k: SHORTEN_PARAM_MAP.get(k,k), fn_params, factory=dict)
        compare_fn_dict = recursive_value_map(lambda val: repr(val).replace(" ", ""), fn_params)
        dir_files = list(self.workingdatapath.glob('*'))
        for filepath in tqdm(dir_files, desc="searching for similar Persistable payloads"):

            # Get filename:
            fn = filepath.name

            # Parse filename, get model parameters:
            try:
                file_fn_type, _, file_fn_dict = parse_standard_filename(fn)
            except ParseException:
                continue

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
