import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from persistable import Persistable
from persistable.data import PersistableParams
from persistable.io import PickleFileIO


@dataclass
class DummyPersistableParams(PersistableParams):
    a: int = 1
    b: str = "hello"


class DummyPersistable(Persistable[Dict[str, Any]]):
    def _generate_payload(self, **untracked_payload_params: Any) -> Dict[str, Any]:
        return dict(a=1, b="test")


class TestPersistable:
    def test_init(self, tmp_path: Path) -> None:
        # GIVEN
        persist_data_dir = tmp_path
        params = DummyPersistableParams()

        # WHEN
        persistable = Persistable(persist_data_dir=persist_data_dir, params=params)

        # THEN
        assert isinstance(persistable, Persistable)
        assert persistable.persist_data_dir == persist_data_dir
        assert persistable.params == params
        assert persistable.payload_name == "persistable"
        assert isinstance(persistable.payload_io, PickleFileIO)

        assert persistable._payload is None

    def test_payload(self, tmp_path: Path) -> None:
        # GIVEN
        persist_data_dir = tmp_path
        params = DummyPersistableParams()
        persistable = DummyPersistable(persist_data_dir=persist_data_dir, params=params)

        # GIVEN expected artifact filepaths
        expected_persistable_filepath = persistable.persist_filepath.with_suffix(persistable.payload_file_suffix)
        expected_params_filepath = persistable.persist_filepath.with_suffix(".params.json")

        # WHEN
        payload = persistable.payload

        # THEN
        assert payload == dict(a=1, b="test")
        assert expected_persistable_filepath.exists()
        assert expected_params_filepath.exists()

        # WHEN
        with expected_params_filepath.open("r") as f:
            params_json = json.load(f)

        assert params_json == dict(a=1, b="hello")
