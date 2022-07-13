import json
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Optional, Collection

from persistable import Persistable
from persistable.data import PersistableParams
from persistable.io import PickleFileIO


@dataclass
class DummyPersistableParams(PersistableParams):
    a: int = 1
    b: str = "hello"


class DummyPersistable(Persistable[Dict[str, Any], DummyPersistableParams]):
    def _generate_payload(self, **untracked_payload_params: Any) -> Dict[str, Any]:
        return dict(a=1, b="test")


class DummyFromOtherPersistablesPersistable(Persistable[Dict[str, Any], DummyPersistableParams]):
    def __init__(
        self,
        data_dir: Path,
        params: DummyPersistableParams,
        *,
        dummy_persistable: DummyPersistable,
        verbose: bool = False,
        logger: Optional[Logger] = None,
    ) -> None:
        super().__init__(data_dir, params, verbose=verbose, logger=logger)
        self.dummy_persistable = dummy_persistable

    @property
    def from_persistable_objs(self) -> Collection[Persistable[Any, Any]]:
        return [self.dummy_persistable]

    def _generate_payload(self, **untracked_payload_params: Any) -> Dict[str, Any]:
        return dict(a=self.params.a, old=self.dummy_persistable.payload)


class TestPersistable:
    def test_init(self, tmp_path: Path) -> None:
        # GIVEN
        data_dir = tmp_path
        params = DummyPersistableParams()

        # WHEN
        persistable = Persistable(data_dir=data_dir, params=params)

        # THEN
        assert isinstance(persistable, Persistable)
        assert persistable.data_dir == data_dir
        assert persistable.params == params
        assert persistable.payload_name == "persistable"
        assert isinstance(persistable.payload_io, PickleFileIO)

        assert persistable._payload is None

    def test_payload(self, tmp_path: Path) -> None:
        # GIVEN
        data_dir = tmp_path
        params = DummyPersistableParams()
        persistable = DummyPersistable(data_dir=data_dir, params=params)

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

    def test_from_persistable_objs(self, tmp_path: Path) -> None:
        # GIVEN
        data_dir = tmp_path
        params = DummyPersistableParams()
        dummy_persistable = DummyPersistable(data_dir=data_dir, params=params)

        # WHEN persistable made from other persistables (here dummy persistable)
        from_other_persistables_persistable = DummyFromOtherPersistablesPersistable(
            data_dir=data_dir, params=params, dummy_persistable=dummy_persistable
        )

        # THEN the params and payload work as expected
        assert from_other_persistables_persistable.params_tree == dict(
            a=1, b="hello", dummy_persistable=dict(a=1, b="hello")
        )
        assert from_other_persistables_persistable.payload == dict(a=1, old=dummy_persistable.payload)
