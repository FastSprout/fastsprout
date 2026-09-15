from typing import Any, dataclass_transform

from pydantic import Field as PydField
from pydantic._internal._model_construction import ModelMetaclass

from fastsprout.core.types.undefined import Undefined

from .field import Field, model_building_context_var

__all__ = [
    "TypedModelMeta",
    "collect_field_descriptors",
    "collect_field_names",
    "convert_field_specifiers",
    "install_descriptors",
    "is_field_annotation",
    "read_annotations",
    "unwrap_field_annotations",
]


def read_annotations(namespace: dict[str, Any]) -> dict[str, Any]:
    """Read class annotations from a metaclass `namespace` dict.

    On Python 3.12-3.13 they live under ``__annotations__``.
    On Python 3.14+ (PEP 749) they may only be available via
    ``__annotate_func__`` / ``__annotate__`` (lazy evaluation).
    """
    anns = namespace.get("__annotations__")
    if anns:
        return anns
    ann_fn = namespace.get("__annotate_func__") or namespace.get("__annotate__")
    if ann_fn is not None:
        try:
            return ann_fn(1) or {}  # 1 == annotationlib.Format.VALUE
        except Exception:
            pass
    return anns if anns is not None else {}


def _resolve_origin(ann: Any) -> type | None:
    """Resolve annotation to the underlying Field subclass (or None)."""
    origin = getattr(ann, "__origin__", None)
    if origin is None:
        return None
    if isinstance(origin, type) and issubclass(origin, Field):
        return origin
    value = getattr(origin, "__value__", None)
    if value is not None:
        inner_origin = getattr(value, "__origin__", None)
        if isinstance(inner_origin, type) and issubclass(inner_origin, Field):
            return inner_origin
    return None


def is_field_annotation(ann: Any) -> bool:
    """Check if annotation is `Field[T]` or any Field subclass."""
    return _resolve_origin(ann) is not None


def collect_field_names(annotations: dict[str, Any]) -> list[str]:
    """Return names of attributes annotated as a Field (any subclass)."""
    return [
        name for name, ann in annotations.items() if is_field_annotation(ann)
    ]


def collect_field_descriptors(
    annotations: dict[str, Any],
) -> dict[str, type[Field]]:
    """Map field name -> exact Field subclass extracted from annotation."""
    out: dict[str, type[Field]] = {}
    for name, ann in annotations.items():
        cls = _resolve_origin(ann)
        if cls is not None:
            out[name] = cls
    return out


def _unwrap_annotation(annotation: Any) -> Any:
    """Field[T, ...] -> T; non-Field -> unchanged."""
    if not is_field_annotation(annotation):
        return annotation
    args = getattr(annotation, "__args__", ())
    return args[0] if args else annotation


def convert_field_specifiers(
    namespace: dict[str, Any], field_names: list[str]
) -> None:
    """Turn `Field(...)` specifiers in the class body into defaults.

    `age: Field[int] = Field(default=0)` is valid for the type checker
    (Field[int] on both sides); the metaclass unwraps the annotation to
    `int`, and this step hands the declared default to the model
    builder — raw value for `default=`, a pydantic FieldInfo for
    `default_factory=`.
    """
    for name in field_names:
        value = namespace.get(name)
        if not isinstance(value, Field):
            continue
        if value.default_factory is not None:
            namespace[name] = PydField(default_factory=value.default_factory)
        elif value.default is not Undefined:
            namespace[name] = value.default
        else:
            namespace[name] = PydField()


def unwrap_field_annotations(
    annotations: dict[str, Any],
    namespace: dict[str, Any] | None = None,
) -> list[str]:
    """Rewrite Field[T, ...] -> T in annotations in-place.

    Returns names of fields that were unwrapped.
    """
    field_names: list[str] = []
    rewritten: dict[str, Any] = {}
    for name, ann in annotations.items():
        if is_field_annotation(ann):
            field_names.append(name)
            rewritten[name] = _unwrap_annotation(ann)
        else:
            rewritten[name] = ann
    annotations.clear()
    annotations.update(rewritten)
    if namespace is not None:
        namespace["__annotations__"] = annotations
    return field_names


def install_descriptors(
    cls: type,
    field_descriptors: dict[str, type[Field]] | list[str],
) -> None:
    """Install Field descriptors of the EXACT declared subclass.

    Accepts either dict[name -> Field subclass] (preserves brick semantics)
    or list[name] (legacy — uses plain Field).

    Idempotent: skips names already holding a Field of the correct subclass.
    """
    if isinstance(field_descriptors, list):
        field_descriptors = {n: Field for n in field_descriptors}

    for name, brick_cls in field_descriptors.items():
        existing = cls.__dict__.get(name)
        if isinstance(existing, brick_cls):
            continue
        descriptor: Field[Any] = brick_cls._descriptor(name)
        descriptor.__set_name__(cls, name)
        setattr(cls, name, descriptor)


@dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
class TypedModelMeta(ModelMetaclass):
    """Unwrap Field[T] -> T before Pydantic builds the model;
    install concrete Field subclass after.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        annotations = read_annotations(namespace)
        field_descriptors = collect_field_descriptors(annotations)
        field_names = unwrap_field_annotations(annotations, namespace)
        convert_field_specifiers(namespace, field_names)
        token = model_building_context_var.set(True)
        try:
            cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        finally:
            model_building_context_var.reset(token)
        install_descriptors(cls, field_descriptors)
        return cls
