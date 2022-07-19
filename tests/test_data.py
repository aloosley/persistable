from dataclasses import dataclass

import pytest

from persistable.data import PersistableParams
from persistable.io import DictEncodable


@dataclass
class DummyPersistableParams(PersistableParams):
    i: int
    f: float
    s: str


@dataclass
class PermutedDummyPersistableParams(PersistableParams):
    i: int
    s: str
    f: float


@dataclass
class DefaultsPersistableParams(PersistableParams):
    i: int = 10
    s: str = "hello"
    f: float = 12.24


class TestPersistableParams:
    def test_init(self) -> None:
        # GIVEN
        i = 10
        f = 12.2
        s = "test"

        # WHEN
        params = DummyPersistableParams(i=i, f=f, s=s)

        # THEN
        assert isinstance(params, PersistableParams)
        assert isinstance(params, DictEncodable)

    def test_to_dict(self) -> None:
        # GIVEN
        params = DefaultsPersistableParams()
        params_dict = params.to_dict()

        # THEN
        assert params_dict == dict(i=10, f=12.24, s="hello")

    @pytest.mark.skip(reason="Permuted params hash inequality feature not yet implements.")
    def test_hash_equality_when_params_permuted(self) -> None:
        # GIVEN
        i = 10
        f = 12.2
        s = "test"

        # WHEN
        params = DummyPersistableParams(i=i, f=f, s=s)
        permuted_params = PermutedDummyPersistableParams(i=i, f=f, s=s)

        # THEN
        assert params.get_md5_hash() == permuted_params.get_md5_hash()
