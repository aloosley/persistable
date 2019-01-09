import persistable
from unittest import TestCase
from pathlib import Path
from persistable.persistload import PersistLoad, PersistLoadBasic, PersistLoadWithParameters
from copy import deepcopy


TESTDATAPATH = Path(persistable.__path__[0]) / "testdata"
TMPTESTDATAPATH = Path(persistable.__path__[0]) / "testdata_tmp" / "test_nested" / "test_nested2"
FN_TYPE = "test_type"
TEST_PAYLOAD = "test_payload"
TEST_PAYLOAD_SIMILAR = "test_2"
FN_PARAMS = {"test1": 2, "test3": {"a": 4, "b": ["why", "ask"]}}
FN_EXT = "ajl"

class TestPersistable(TestCase):

    def test_init_and_persist_with_new_folder(
            self,
            new_intermediate_data_path=TMPTESTDATAPATH,
            payload=TEST_PAYLOAD,
            fn_params=FN_PARAMS,
            fn_type=FN_TYPE
    ):
        """
        Tests that persist load can initialize into nested directories that do not exist.

        Parameters
        ----------
        new_intermediate_data_path

        Returns
        -------

        """

        # If directory exists, remove it for test:
        if new_intermediate_data_path.exists():
            # Remove files and dir:
            [f.unlink() for f in new_intermediate_data_path.glob("*")]
            new_intermediate_data_path.rmdir()

        pl = PersistLoadWithParameters(new_intermediate_data_path, verbose=False, dill=False)
        pl.persist(payload, fn_type, fn_params)

        self.assertTrue(new_intermediate_data_path.exists())
        self.assertEqual(pl.workingdatapath, new_intermediate_data_path)

    def test_persist_basic(self, intermediate_data_path=TESTDATAPATH, payload=TEST_PAYLOAD, fn_type=FN_TYPE):
        """
        Tests that basic persist feature creates serialized payload-file as expected.

        Parameters
        ----------
        intermediate_data_path  : Path
            location to persist/load intermediate test payloads

        Returns
        -------

        """

        # Instantiate and persist payload:
        pl = PersistLoadBasic(intermediate_data_path, verbose=False, dill=False)
        pl.persist(payload, fn_type)

        # Check file created:
        persisted_filepath = intermediate_data_path / f"{fn_type}.pkl"
        self.assertTrue(persisted_filepath.exists())

    def test_load_basic(self, intermediate_data_path=TESTDATAPATH, saved_payload=TEST_PAYLOAD, fn_type=FN_TYPE):
        """
        Given basic persist feature serializes a payload in file, this tests if it can be loaded and if the payload
        loads as expected.

        Parameters
        ----------
        intermediate_data_path  : Path
            location to persist/load intermediate test payloads

        Returns
        -------

        """

        # Persist payload:
        self.test_persist_basic(payload=saved_payload)

        # Instantiate and load payload:
        pl = PersistLoadBasic(intermediate_data_path, verbose=False, dill=False)
        test_payload = pl.load(fn_type)

        # Check payload loaded properly:
        self.assertEqual(test_payload, saved_payload)

    def test_persist_with_params(self,
                                 intermediate_data_path=TESTDATAPATH, payload=TEST_PAYLOAD,
                                 fn_type=FN_TYPE):
        """
        Tests that persist with parameters creates serialized payload-file as expected.

        Parameters
        ----------
        intermediate_data_path  : Path
            location to persist/load intermediate test payloads

        Returns
        -------

        """

        # Instantiate and persist payload:
        pl = PersistLoadWithParameters(intermediate_data_path, verbose=False, dill=False)
        pl.persist(payload, fn_type, FN_PARAMS, FN_EXT)

        # Check file created:
        persisted_filepath = intermediate_data_path / f"{fn_type}{{test1=2,test3={{a=4,b=['why', 'ask']}}}}.{FN_EXT}"
        self.assertTrue(persisted_filepath.exists())

    def test_load_with_params(self, intermediate_data_path=TESTDATAPATH, saved_payload=TEST_PAYLOAD, fn_type=FN_TYPE):
        """
        Given Persistable serialized a payload to file, this tests if it can be loaded and if the payload
        loads as expected.

        Parameters
        ----------
        intermediate_data_path  : Path
            location to persist/load intermediate test payloads

        Returns
        -------

        """

        # Persist payload:
        self.test_persist_with_params(payload=saved_payload)

        # Instantiate Persistload and load payload:
        pl = PersistLoadWithParameters(intermediate_data_path, verbose=False, dill=False)
        test_payload = pl.load(fn_type, FN_PARAMS, fn_ext=FN_EXT)

        # Check payload loaded properly:
        self.assertEqual(test_payload, saved_payload)

    def test_load_similar_with_params(self, intermediate_data_path=TMPTESTDATAPATH,
                                      payload=TEST_PAYLOAD_SIMILAR,
                                      fn_type=FN_TYPE, fn_params=FN_PARAMS):
        """

        Parameters
        ----------
        intermediate_data_path
        payload

        Returns
        -------

        """

        # Persist to empty folder:
        self.test_init_and_persist_with_new_folder(new_intermediate_data_path=intermediate_data_path,
                                                   payload=payload,
                                                   fn_params=fn_params)

        # Remove a parameter key to load similar file:
        reduced_fn_params = deepcopy(fn_params)
        del reduced_fn_params[list(sorted(fn_params.keys()))[0]]
        pl = PersistLoadWithParameters(intermediate_data_path)
        obj = pl.load(fn_type, reduced_fn_params)

        self.assertEqual(obj, payload)
