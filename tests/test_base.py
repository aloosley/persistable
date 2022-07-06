from dataclasses import dataclass
from pathlib import Path

from persistable import Persistable
from persistable.data import PersistableParams


@dataclass
class DummyPersistableParams(PersistableParams):
    a = 1
    b = "hello"


class TestPersistable:
    def test_init(self, tmp_dir: Path) -> None:
        # GIVEN
        persist_data_dir = tmp_dir
        params = DummyPersistableParams()

        Persistable(persist_data_dir=persist_data_dir, params=params)


'''
TESTDATAPATH = Path(persistable.__path__[0]) / "testdata"
TMPTESTDATAPATH = Path(persistable.__path__[0]) / "tmptestdata"
TEST_PAYLOAD = "test_payload"
TEST_PARAMS = {"test1": 2, "test3": {"a": 4, "b": ["why", "ask"]}}
TEST_PARAMS2 = {"test1": 2, "test5": {"c": 4, "b": ["why", "ask"]}}


class TestPersistableOld(TestCase):

    def test_payload_init(self, p=None, p_name="test", workingdatapath=TESTDATAPATH):
        """

        Parameters
        ----------
        p               :
        workingdatapath :

        Returns
        -------

        """
        # Check payload:
        if p is None:
            p = Persistable(p_name, workingdatapath=workingdatapath)
        self.assertTrue(isinstance(p.payload, defaultdict))

    def test_recursive_default_dict_payload(self, p=None, p_name="test", workingdatapath=TESTDATAPATH):
        """

        Parameters
        ----------
        p
        workingdatapath

        Returns
        -------

        """
        # Check default payload as recursive def. dict:

        if p is None:
            p = Persistable(p_name, workingdatapath=workingdatapath)
        key1 = "key1"
        key2 = "key2"
        p.payload[key1][key2] = "test"

        # Payload_keys
        self.assertListEqual(list(p.payload.keys()), [key1])
        self.assertListEqual(list(p.payload[key1].keys()), [key2])
        self.assertListEqual(list(p.payload.keys()), list(p.payload_keys))

    def test_reset_payload(self, p_name="test", workingdatapath=TESTDATAPATH):
        """

        Parameters
        ----------
        workingdatapath

        Returns
        -------

        """
        p = Persistable(p_name, workingdatapath=workingdatapath)
        key1 = "key1"
        key2 = "key2"
        p.payload[key1][key2] = "test"

        p.reset_payload()

        self.test_payload_init(p)
        self.test_recursive_default_dict_payload(p)

    def test_persistload_functionality(self, p_name="test", params=TEST_PARAMS,
                                       workingdatapath=TESTDATAPATH):

        p = Persistable(p_name, params=params, workingdatapath=workingdatapath)
        key1 = "key1"
        key2 = "key2"
        p.payload[key1][key2] = "test"

        # Persist:
        p.persist()

        # Get Filename:
        fn = default_standard_filename(p_name, **params)

        # Check file persisted:
        self.assertTrue((workingdatapath / fn).exists())

        # Load to new persistable:
        p2 = Persistable(p_name, params=params, workingdatapath=workingdatapath)
        p2.load()

        # Check both payloads are the same:
        self.assertDictEqual(p.payload, p2.payload)

    def test_update_fn_params(self, p_name="test", old_params=TEST_PARAMS, new_params=TEST_PARAMS2,
                              new_intermediate_data_path=TMPTESTDATAPATH):

        # Create clear directory:
        # If directory exists, remove it for test:
        if new_intermediate_data_path.exists():
            # Remove files and dir:
            [f.unlink() for f in new_intermediate_data_path.glob("*")]
            new_intermediate_data_path.rmdir()

        # Persist Payload:
        p = Persistable(p_name, params=old_params, workingdatapath=new_intermediate_data_path)
        p.payload = TEST_PAYLOAD
        p.persist()

        old_fn = default_standard_filename(p_name, **old_params)
        self.assertTrue((new_intermediate_data_path / old_fn).exists())

        # Update fn params and keep old file:
        p.update_fn_params(new_params, delete_old=False)
        new_fn = default_standard_filename(p_name, **new_params)
        self.assertTrue((new_intermediate_data_path / old_fn).exists())
        self.assertTrue((new_intermediate_data_path / new_fn).exists())

        # Update fn params when file already exists:
        p = Persistable(p_name, params=old_params, workingdatapath=new_intermediate_data_path)
        with self.assertRaises(FileExistsError):
            p.update_fn_params(new_params, delete_old=True)

        # Delete new file and update fn params and remove old file:
        new_fn = default_standard_filename(p_name, **new_params)
        (new_intermediate_data_path / new_fn).unlink()
        p = Persistable(p_name, params=old_params, workingdatapath=new_intermediate_data_path)
        p.update_fn_params(new_params, delete_old=True)
        self.assertFalse((new_intermediate_data_path / old_fn).exists())
        self.assertTrue((new_intermediate_data_path / new_fn).exists())

        # Test fn_params updated:
        self.assertDictEqual(p.fn_params, new_params)

        # Load new persistable and check payload:
        p2 = Persistable(p_name, params=new_params, workingdatapath=new_intermediate_data_path)
        p2.load()
        self.assertEqual(TEST_PAYLOAD, p2.payload)

    def test_update_payload_name(self, old_p_name="test", new_p_name="test2", params=TEST_PARAMS,
                              new_intermediate_data_path=TMPTESTDATAPATH):

        # Create clear directory:
        # If directory exists, remove it for test:
        if new_intermediate_data_path.exists():
            # Remove files and dir:
            [f.unlink() for f in new_intermediate_data_path.glob("*")]
            new_intermediate_data_path.rmdir()

        # Persist Payload:
        p = Persistable(old_p_name, params=params, workingdatapath=new_intermediate_data_path)
        p.payload = TEST_PAYLOAD
        p.persist()

        old_fn = default_standard_filename(old_p_name, **params)
        self.assertTrue((new_intermediate_data_path / old_fn).exists())

        # Update fn params and keep old file:
        p.update_payload_name(new_p_name, delete_old=False)
        new_fn = default_standard_filename(new_p_name, **params)
        self.assertTrue((new_intermediate_data_path / old_fn).exists())
        self.assertTrue((new_intermediate_data_path / new_fn).exists())

        # Update fn params when file already exists:
        p = Persistable(old_p_name, params=params, workingdatapath=new_intermediate_data_path)
        with self.assertRaises(FileExistsError):
            p.update_payload_name(new_p_name, delete_old=True)

        # Delete new file and update fn params and remove old file:
        new_fn = default_standard_filename(new_p_name, **params)
        (new_intermediate_data_path / new_fn).unlink()
        p = Persistable(old_p_name, params=params, workingdatapath=new_intermediate_data_path)
        p.update_payload_name(new_p_name, delete_old=True)
        self.assertFalse((new_intermediate_data_path / old_fn).exists())
        self.assertTrue((new_intermediate_data_path / new_fn).exists())

        # Test fn_params updated:
        self.assertEqual(p.payload_name, new_p_name)

        # Load new persistable and check payload:
        p2 = Persistable(new_p_name, params=params, workingdatapath=new_intermediate_data_path)
        p2.load()
        self.assertEqual(TEST_PAYLOAD, p2.payload)

    def test_params_validation(self) -> None:
        # GIVEN
        params = dict(contains_slash="this/has/a/slash", ok=1)
        working_dir = Path(".")

        # WHEN and THEN
        with self.assertRaises(ValueError):
            Persistable(payload_name="test", params=params, workingdatapath=working_dir)
'''
