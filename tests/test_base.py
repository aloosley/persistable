import json
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from persistable import Persistable
from persistable.data import PersistableParams
from persistable.exceptions import NoPayloadError, InvalidPayloadError, InvalidPayloadWarning
from persistable.io import PickleFileIO


@dataclass
class DummyPersistableParams(PersistableParams):
    a: int = 1
    b: str = "hello"


class DummyPersistable(Persistable[Dict[str, Any], DummyPersistableParams]):
    def _generate_payload(self, **untracked_payload_params: Any) -> Dict[str, Any]:
        return dict(a=1, b="test")

    def _validate_payload(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise InvalidPayloadError


class DummyPersistableWithTrackedDependencies(Persistable[Dict[str, Any], DummyPersistableParams]):
    def __init__(
        self,
        data_dir: Path,
        params: DummyPersistableParams,
        *,
        dummy_persistable: DummyPersistable,
        verbose: bool = False,
        logger: Optional[Logger] = None,
    ) -> None:
        super().__init__(
            data_dir, params, tracked_persistable_dependencies=(dummy_persistable,), verbose=verbose, logger=logger
        )
        self.dummy_persistable = dummy_persistable

    def _generate_payload(self, **untracked_payload_params: Any) -> Dict[str, Any]:
        return dict(a=self.params.a, old=self.dummy_persistable.payload)


class TestPersistable:
    def test_init(self, tmp_path: Path) -> None:
        # GIVEN
        data_dir = tmp_path
        params = DummyPersistableParams()

        # WHEN
        persistable = Persistable(data_dir=data_dir, params=params, tracked_persistable_dependencies=None)

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
        persistable = DummyPersistable(data_dir=data_dir, params=params, tracked_persistable_dependencies=None)

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

    def test_tracked_persistable_dependencies(self, tmp_path: Path) -> None:
        # GIVEN
        data_dir = tmp_path
        params = DummyPersistableParams()
        dummy_persistable = DummyPersistable(data_dir=data_dir, params=params, tracked_persistable_dependencies=None)

        # WHEN persistable made from other persistables (here dummy persistable)
        from_other_persistables_persistable = DummyPersistableWithTrackedDependencies(
            data_dir=data_dir, params=params, dummy_persistable=dummy_persistable
        )

        # THEN the payload and params work as expected
        assert from_other_persistables_persistable.payload == dict(a=1, old=dummy_persistable.payload)
        assert from_other_persistables_persistable.params_tree == dict(
            a=1, b="hello", dummy_persistable=dict(a=1, b="hello")
        )

    def test_persist_filepath_determined_by_both_params_tree_and_payload_name(self, tmp_path: Path) -> None:
        # GIVEN some persistable instances
        data_dir = tmp_path
        params = DummyPersistableParams()
        dummy_persistable = DummyPersistable(data_dir=data_dir, params=params, tracked_persistable_dependencies=None)

        params_2 = DummyPersistableParams(a=2, b="world")
        dummy_persistable_2 = DummyPersistable(
            data_dir=data_dir, params=params_2, tracked_persistable_dependencies=None
        )

        # WHEN and THEN
        assert dummy_persistable.params_tree == params.to_dict()
        assert dummy_persistable.persist_filepath == data_dir / "dummy_persistable(6a0f2e637a47f02428f19726be8541a1)"

        # WHEN payload_name changed
        dummy_persistable.payload_name = "another"

        # THEN persist filepath has changed (hash should be determined from params_tree and payload_name)
        assert dummy_persistable.params_tree == params.to_dict()
        assert dummy_persistable.persist_filepath == data_dir / "another(e15cab0e04c56c6deddb1ac7bc5e5956)"

        # WHEN params changed
        dummy_persistable.params.a += 10

        # THEN persist filepath has changed (hash should be determined from params_tree and payload_name)
        assert dummy_persistable.params_tree == params.to_dict()
        assert dummy_persistable.persist_filepath == data_dir / "another(bd9f250dac257114768e128ed4d9eb96)"

        # WHEN the tracked persistable dependencies change
        dummy_persistable.tracked_persistable_dependencies = [dummy_persistable_2]

        # THEN the params_tree changes and the persist_filepath also changes accordingly
        assert dummy_persistable.params == params
        assert dummy_persistable.params_tree == params.to_dict() | {
            dummy_persistable_2.payload_name: params_2.to_dict()
        }
        assert dummy_persistable.persist_filepath == data_dir / "another(e1815602bc39616f5378f6305ef2d8ee)"

    def test_multilevel_params_tree(self, tmp_path: Path) -> None:
        # GIVEN some persistable instances that depend on each other
        data_dir = tmp_path

        params1 = DummyPersistableParams(a=1, b="one")
        params2 = DummyPersistableParams(a=2, b="two")
        params3 = DummyPersistableParams(a=3, b="three")

        dummy_persistable1 = DummyPersistable(
            payload_name="first", data_dir=data_dir, params=params1, tracked_persistable_dependencies=None
        )
        dummy_persistable2 = DummyPersistable(
            payload_name="second",
            data_dir=data_dir,
            params=params2,
            tracked_persistable_dependencies=[dummy_persistable1],
        )
        dummy_persistable3 = DummyPersistable(
            payload_name="third",
            data_dir=data_dir,
            params=params3,
            tracked_persistable_dependencies=[dummy_persistable1, dummy_persistable2],
        )

        # WHEN getting params_tree, THEN the params tree is as expected
        assert dummy_persistable1.params_tree == dict(a=1, b="one")
        assert dummy_persistable2.params_tree == dict(a=2, b="two", first=dict(a=1, b="one"))
        assert dummy_persistable3.params_tree == dict(
            a=3, b="three", first=dict(a=1, b="one"), second=dict(a=2, b="two", first=dict(a=1, b="one"))
        )

    def test_payload_validation(self, tmp_path: Path) -> None:
        # GIVEN persistable
        data_dir = tmp_path
        params = DummyPersistableParams()
        dummy_persistable = DummyPersistable(data_dir=data_dir, params=params, tracked_persistable_dependencies=None)

        # GIVEN valid and invalid payloads
        valid_payload = dict(a=1, b=2)
        invalid_payload = [dict(a=1, b=2)]

        # WHEN and THEN
        with pytest.raises(NoPayloadError):
            dummy_persistable.validate_payload()
        dummy_persistable.validate_payload(payload=valid_payload)
        with pytest.raises(InvalidPayloadError):
            dummy_persistable.validate_payload(payload=invalid_payload)

    def test_validate_payload_on_load(self, tmp_path: Path) -> None:
        # GIVEN persistable
        data_dir = tmp_path
        params = DummyPersistableParams()
        dummy_persistable = DummyPersistable(data_dir=data_dir, params=params, tracked_persistable_dependencies=None)

        # GIVEN invalid payload that is persisted
        invalid_payload = [dict(a=1, b=2)]
        dummy_persistable._payload = invalid_payload
        dummy_persistable.persist()

        # WHEN
        with pytest.warns(InvalidPayloadWarning):
            dummy_persistable.load(warn_if_validation_fails=True)
        with pytest.raises(InvalidPayloadError):
            dummy_persistable.load(warn_if_validation_fails=False)
