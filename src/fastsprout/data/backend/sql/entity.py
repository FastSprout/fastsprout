from contextlib import AbstractAsyncContextManager
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Self,
    dataclass_transform,
    get_args,
)

from sqlalchemy import MetaData
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import registry as sa_registry
from sqlmodel import Field as SQLPydField
from sqlmodel import SQLModel, Table
from sqlmodel.main import RelationshipInfo, SQLModelMetaclass
from typing_extensions import TypeVar

from fastsprout.core import Field, InternalField, ReadField, Schema
from fastsprout.core.dto import is_dto_base
from fastsprout.core.fields.field import (
    check_field_visibility,
    model_building_context_var,
)
from fastsprout.core.fields.has_orm import HasOrm
from fastsprout.core.fields.metaclass import (
    collect_field_descriptors,
    convert_field_specifiers,
    read_annotations,
    unwrap_field_annotations,
)
from fastsprout.core.types import IdentificatorType
from fastsprout.data.backend.implementation import Signpost
from fastsprout.data.entity import Entitieable, Signpostable

__all__ = [
    "SQL_ENTITY_REGISTRY",
    "SQLEntity",
    "SQLSignpost",
    "SQLSource",
    "TypedSQLMeta",
    "validate_source",
    "validate_source_type",
]

type SQLSource = Signpostable[AbstractAsyncContextManager[AsyncSession]]

IDT = TypeVar("IDT", bound=IdentificatorType)
SourceT = TypeVar(
    "SourceT",
    bound=Signpostable[AbstractAsyncContextManager[AsyncSession]],
    default=Signpostable[AbstractAsyncContextManager[AsyncSession]],
    covariant=True,
)

SQL_ENTITY_REGISTRY = sa_registry(metadata=MetaData())


def mro_field_names(cls: type) -> list[str]:
    """All Field-annotated names declared anywhere in the class's MRO."""
    seen: set[str] = set()
    out: list[str] = []
    for klass in cls.__mro__:
        for fname in klass.__dict__.get("__fastsprout_fields__", ()):
            if fname not in seen:
                seen.add(fname)
                out.append(fname)
    return out


def inject_relationship_keys(
    name: str,
    annotations: dict[str, Any],
    namespace: dict[str, Any],
) -> list[str]:
    keys: list[str] = []
    for fname, annotation in tuple(annotations.items()):
        relation = namespace.get(fname)
        if not isinstance(relation, RelationshipInfo) or not getattr(
            relation, "__fastsprout_auto__", False
        ):
            continue
        optional = type(None) in get_args(annotation)
        target = next(
            (arg for arg in get_args(annotation) if arg is not type(None)),
            annotation,
        )
        table = getattr(target, "__table__", None)
        model_fields = getattr(target, "model_fields", {})
        if table is None or "id" not in model_fields:
            raise TypeError(
                f"Relationship {name}.{fname} requires a mapped entity"
            )
        fk_name = f"{fname}_id"
        if fk_name in annotations or fk_name in namespace:
            raise TypeError(
                f"Relationship {name}.{fname} already has {fk_name}"
            )
        id_type = model_fields["id"].annotation
        annotations[fk_name] = id_type | None
        keys.append(fk_name)
        namespace[fk_name] = SQLPydField(
            default=None,
            foreign_key=f"{table.name}.id",
            nullable=optional,
        )
    return keys


@dataclass_transform(
    kw_only_default=True, field_specifiers=(Field, SQLPydField)
)
class TypedSQLMeta(SQLModelMetaclass):
    """SQLModel metaclass + fastsprout Field installation.

    1. __new__: unwrap Field[T] → T for Pydantic/SQLModel
    2. __init__: capture SA InstrumentedAttribute and install Field carrying it
    """

    if not TYPE_CHECKING:

        def __getattr__(cls, name: str) -> Any:  # noqa: N805  # metaclass
            check_field_visibility(cls, name)
            return super().__getattr__(name)

    def __new__(mcs, name, bases, namespace, **kwargs):
        if any(is_dto_base(base) for base in bases):
            return type.__new__(
                mcs, name, bases, namespace, init=kwargs.get("init", False)
            )
        if (
            "table" not in kwargs
            and "__pydantic_generic_metadata__" not in kwargs
            and any(isinstance(b, TypedSQLMeta) for b in bases)
        ):
            kwargs["table"] = True
        annotations = read_annotations(namespace)
        field_descriptors = collect_field_descriptors(annotations)
        field_names = list(field_descriptors)
        unwrap_field_annotations(annotations, namespace)
        convert_field_specifiers(namespace, field_names)
        relationship_keys = inject_relationship_keys(
            name, annotations, namespace
        )
        field_names.extend(relationship_keys)

        for fname in field_names:
            if isinstance(annotations.get(fname), TypeVar):
                annotations[fname] = Any
        namespace["__fastsprout_fields__"] = field_names
        namespace["__fastsprout_descriptors__"] = {
            **field_descriptors,
            **dict.fromkeys(relationship_keys, InternalField),
        }
        token = model_building_context_var.set(True)
        try:
            return super().__new__(mcs, name, bases, namespace, **kwargs)
        finally:
            model_building_context_var.reset(token)

    def __init__(cls, name, bases, namespace, **kwargs):  # noqa: N805  # metaclass
        if any(is_dto_base(base) for base in bases):
            return
        # SQLModel drops this keyword before delegating to Pydantic.
        if metadata := kwargs.get("__pydantic_generic_metadata__"):
            cls.__pydantic_generic_metadata__ = metadata
        super().__init__(name, bases, namespace, **kwargs)
        if hasattr(cls, "__table__"):
            model_fields = getattr(cls, "model_fields", {})
            targets = [n for n in mro_field_names(cls) if n in model_fields]
            mapper_attrs = sa_inspect(cls).attrs
        else:
            targets = cls.__dict__.get("__fastsprout_fields__", [])
            mapper_attrs = {}
        descriptors = {
            name: descriptor
            for base in reversed(cls.__mro__)
            for name, descriptor in vars(base)
            .get("__fastsprout_descriptors__", {})
            .items()
        }
        for fname in targets:
            orm_attr = (
                mapper_attrs[fname].class_attribute
                if fname in mapper_attrs
                else None
            )
            descriptor: Field[Any] = descriptors.get(fname, Field).descriptor(
                fname, orm_attr
            )
            descriptor.__set_name__(cls, fname)
            setattr(cls, fname, descriptor)


class SQLSignpost(Signpost[AbstractAsyncContextManager[AsyncSession]]):
    def bind[ID: IdentificatorType](
        self, entity: "type[SQLEntity[ID, Self]]"
    ) -> None:
        """Assign this signpost after checking the entity's declared source."""
        validate_source_type(entity, self)
        entity.__signpost__ = self


class SQLEntity(
    SQLModel,
    Schema,
    HasOrm[Mapped[Any]],
    Entitieable[IDT],
    # SQLModel requires legacy generics for inherited model parameters.
    Generic[IDT, SourceT],
    metaclass=TypedSQLMeta,
    registry=SQL_ENTITY_REGISTRY,
):
    """SQL entity with an optional signpost type checked on declaration."""

    if TYPE_CHECKING:
        __table__: ClassVar[Table]

    __signpost__: ClassVar[
        Signpostable[AbstractAsyncContextManager[AsyncSession]]
    ]

    id: ReadField[IDT]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        validate_source(cls)


def validate_source(
    entity: type[SQLEntity[IDT, SourceT]], source: SQLSource | None = None
) -> None:
    """Check the current signpost against the entity's declared source type."""
    if source is not None and entity.__signpost__ is not source:
        raise TypeError("SQL queries require their declared signpost")
    if hasattr(entity, "__signpost__"):
        validate_source_type(entity, entity.__signpost__)


def validate_source_type(
    entity: type[SQLEntity[IDT, SourceT]], source: SQLSource
) -> None:
    """Validate a candidate before changing the entity's source binding."""
    for base in entity.__mro__:
        metadata = vars(base).get("__pydantic_generic_metadata__", {})
        arguments = metadata.get("args", ())
        if len(arguments) == 2 and metadata.get("origin") is SQLEntity:
            source_type = arguments[1]
            if (
                source_type is not Any
                and isinstance(source_type, type)
                and not isinstance(source, source_type)
            ):
                raise TypeError(
                    f"{entity.__name__}.__signpost__ must be an instance of {source_type.__name__}"
                )
