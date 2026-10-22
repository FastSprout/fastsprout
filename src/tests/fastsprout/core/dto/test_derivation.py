from collections.abc import Callable

import pytest

from fastsprout.core import (
    BaseSchema,
    Field,
    ReadDTO,
    ReadWriteDTO,
    Schema,
    WriteDTO,
    derive_read_dto,
    derive_read_write_dto,
    derive_write_dto,
    typed_fields,
)
from fastsprout.core.dto.conversion import (
    prepare_create,
    project_read,
    supplied_names,
)
from fastsprout.testing.core import given, then, when


class Source(BaseSchema):
    name: Field[str]


class ForeignInput(BaseSchema):
    other: str


class TestConversion:
    @when("a schema conversion requests an unrelated read or write field")
    def rejected(self, reading: bool) -> TypeError | AttributeError | None:
        try:
            if reading:
                project_read(Source(name="source"), ForeignInput)
            else:
                prepare_create(
                    Source, ForeignInput, ForeignInput(other="value")
                )
        except (TypeError, AttributeError) as error:
            return error
        return None

    @pytest.mark.parametrize(
        "reading, error, message",
        [(True, TypeError, "ReadDTO"), (False, AttributeError, "not writable")],
    )
    @then("conversion rejects incompatible projections and forbidden writes")
    def test_rejected(
        self,
        rejected: TypeError | AttributeError | None,
        error: type[TypeError] | type[AttributeError],
        message: str,
    ) -> None:
        assert isinstance(rejected, error)
        assert message in str(rejected)

    @when("the supplied fields of a read DTO are inspected")
    def supplied(self) -> set[str]:
        return supplied_names(derive_read_dto(Source)(name="source"))

    @then("DTO supplied fields contain their initialized values")
    def test_supplied(self, supplied: set[str]) -> None:
        assert supplied == {"name"}


@typed_fields
class PlainSource(Schema):
    name: Field[str] = Field(default="name")
    tags: Field[list[str]] = Field(default_factory=list)


class TestPlainDefaults:
    @given("a plain typed source with descriptor defaults")
    def source(self) -> type[PlainSource]:
        return PlainSource

    @when("two derived DTOs are created and one default list is changed")
    def created(
        self, source: type[PlainSource]
    ) -> tuple[PlainSource, PlainSource]:
        model = derive_read_dto(source)
        first, second = model(), model()
        first.tags.append("changed")
        return first, second

    @then("DTOs preserve scalar defaults and isolate factory values")
    def test_defaults(self, created: tuple[PlainSource, PlainSource]) -> None:
        first, second = created
        assert first.name == second.name == "name"
        assert first.tags == ["changed"]
        assert second.tags == []
        assert isinstance(first, ReadDTO)

    @when("the derivation cache contains an unrelated class")
    def corrupted_cache(
        self, source: type[PlainSource], monkeypatch: pytest.MonkeyPatch
    ) -> TypeError | None:
        monkeypatch.setattr(
            source, "__fastsprout_ReadDTO__", str, raising=False
        )
        try:
            derive_read_dto(source)
        except TypeError as error:
            return error
        return None

    @then("a corrupted cache cannot return a DTO of another source")
    def test_corrupted_cache(self, corrupted_cache: TypeError | None) -> None:
        assert isinstance(corrupted_cache, TypeError)
        assert "must derive from its source" in str(corrupted_cache)


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
