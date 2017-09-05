from .util.logging import get_logger
from .util.os_util import default_standard_filename
import pickle


class PersistLoad:
    def __init__(self, workingdatapath):
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
        self.logger = get_logger(self.__class__.__name__)

    def persist(self):
        raise NotImplementedError("persist must be implemented")

    def load(self):
        raise NotImplementedError("load must be implemented")

    def get_type(self):
        return self.__class__.__name__.split("PersistLoad")[-1]


class PersistLoadBasic(PersistLoad):
    def __init__(self, workingdatapath):
        super().__init__(workingdatapath)

    def persist(self, obj, name):
        self.logger.info(f"PERSISTING {name}")
        with open(self.workingdatapath / f"{name}.pkl", 'wb') as f:
            pickle.dump(obj, f)

    def load(self, name):
        self.logger.info(f"LOADING {name}")
        with open(self.workingdatapath / f"{name}.pkl", 'rb') as f:
            return pickle.load(f)


class PersistLoadWithParameters(PersistLoad):

    def __init__(self, workingdatapath):
        super().__init__(workingdatapath)

    def persist(self, obj, fn_type, fn_params, fn_ext=None):

        # Get filename:
        fn = default_standard_filename(fn_type, fn_ext=fn_ext, **fn_params)
        self.logger.info("PERSISTING %s to %s" % (fn_type, fn))

        # Persist:
        # patched_pickle_dump(obj, os.path.join(self.local_save_dir, fn))
        with open(self.workingdatapath / fn, 'wb') as f:
            pickle.dump(obj, f)

    def load(self, fn_type, fn_params, fn_ext=None):

        # Get filename:
        fn = default_standard_filename(fn_type, fn_ext=fn_ext, **fn_params)
        self.logger.info("Attempting to LOAD %s from %s" % (fn_type, fn))

        # First attempt to find exact file:
        try:
            # load_obj = patched_pickle_load(os.path.join(self.local_save_dir, fn))
            with open(self.workingdatapath / fn, 'rb') as f:
                load_obj = pickle.load(f)
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
