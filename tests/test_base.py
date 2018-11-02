import persistable
from unittest import TestCase
from pathlib import Path
from persistable import Persistable
from persistable.util.dict import defaultdict
from persistable.util.os_util import default_standard_filename


TESTDATAPATH = Path(persistable.__path__[0]) / "testdata"

class TestPersistable(TestCase):

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

    def test_persistload(self, p_name="test", params=dict(test_param="test"), workingdatapath=TESTDATAPATH):

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