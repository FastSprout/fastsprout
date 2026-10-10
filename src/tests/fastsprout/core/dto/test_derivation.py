from collections.abc import Callable

import pytest

from fastsprout.core import (
    BaseSchema,
    Field,
    ReadDTO,
    ReadWriteDTO,
    WriteDTO,
    derive_read_dto,
    derive_read_write_dto,
    derive_write_dto,
)


class Source(BaseSchema):
    name: Field[str]


@pytest.mark.parametrize(
    ("derive", "mode"),
    [
        (derive_read_dto, ReadDTO),
        (derive_write_dto, WriteDTO),
        (derive_read_write_dto, ReadWriteDTO),
    ],
)
def test_derivation_caches_each_source_and_mode_separately(
    derive: Callable[[type[Source]], type[Source]],
    mode: type[ReadDTO | WriteDTO | ReadWriteDTO],
) -> None:
    parent = derive(Source)

    class ExtendedSource(Source):
        label: Field[str] = Field(default="label")

    child = derive(ExtendedSource)
    assert derive(Source) is parent
    assert derive(ExtendedSource) is child
    assert issubclass(child, mode)
    assert child.__fastsprout_source__ is ExtendedSource
    assert "label" in child.__fastsprout_definition__.allowed
    assert child is not parent
    variants = {
        derive_read_dto(Source),
        derive_write_dto(Source),
        derive_read_write_dto(Source),
    }
    assert len(variants) == 3
