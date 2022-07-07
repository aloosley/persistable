from dataclasses import dataclass

import pytest

from persistable.data import PersistableParams
from persistable.io import DictEncodable


@dataclass
class DummyPersistableParameters(PersistableParams):
    i: int
    f: float
    s: str


@dataclass
class PermutedDummyPersistableParameters(PersistableParams):
    i: int
    s: str
    f: float


class TestPersistableParams:
    def test_init(self) -> None:
        # GIVEN
        i=10
        f=12.2
        s="test"

        # WHEN
        params = DummyPersistableParameters(i=i, f=f, s=s)

        # THEN
        assert isinstance(params, PersistableParams)
        assert isinstance(params, DictEncodable)

    @pytest.mark.skip(reason="Permuted params hash inequality feature not yet implements.")
    def test_hash_equality_when_params_permuted(self) -> None:
        # GIVEN
        i=10
        f=12.2
        s="test"

        # WHEN
        params = DummyPersistableParameters(i=i, f=f, s=s)
        permuted_params = PermutedDummyPersistableParameters(i=i, f=f, s=s)

        # THEN
        assert params.get_md5_hash() == permuted_params.get_md5_hash()
